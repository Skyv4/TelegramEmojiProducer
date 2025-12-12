
import struct
from io import BytesIO
import os

# --- Constants ---
EBML_ID_EBML = 0x1A45DFA3
EBML_ID_SEGMENT = 0x18538067
EBML_ID_TRACKS  = 0x1654AE6B
EBML_ID_TRACKENTRY = 0xAE
EBML_ID_VIDEO = 0xE0
EBML_ID_ALPHAMODE = 0x53C0
EBML_ID_CLUSTER = 0x1F43B675
EBML_ID_SIMPLEBLOCK = 0xA3
EBML_ID_BLOCKGROUP  = 0xA0
EBML_ID_BLOCK       = 0xA1
EBML_ID_BLOCKADDITIONS = 0x75A1
EBML_ID_BLOCKMORE   = 0xA6
EBML_ID_BLOCKADDID  = 0xEE
EBML_ID_BLOCKADDITIONAL = 0xA5
EBML_ID_SEEKHEAD = 0x114D9B74
EBML_ID_CUES = 0x1C53BB6B
EBML_ID_VOID = 0xEC
EBML_ID_TAGS = 0x1254C367


# --- Utils ---
def encode_vint(num):
    if num < 0: raise ValueError("VINT must be positive")
    
    length = 1
    limit = 127
    while num >= limit and length < 8:
        length += 1
        limit = (1 << (7 * length)) - 1
        
    if num > limit:
        raise ValueError(f"Value {num} exceeds VINT capacity")
    
    marker = 1 << (7 * length + (8 - length) - 1) # This is getting complicated logic-wise due to bit position
    # Simpler:
    # Marker is 0x80 at first byte, shifted right by (length-1)
    marker_byte = 0x80 >> (length - 1)
    # Shift to position at top of VINT
    marker_val = marker_byte << (8 * (length - 1))
    
    val = num | marker_val
    return val.to_bytes(length, 'big')

def read_vint(stream):
    start_byte = stream.read(1)
    if not start_byte: return None, 0
    val = start_byte[0]
    length = 0
    mask = 0x80
    while mask and not (val & mask):
        mask >>= 1
        length += 1
    length += 1 # 1-based count
    
    # Extract value
    value = val & ( (1 << (8 - length)) - 1 )
    for _ in range(length - 1):
        b = stream.read(1)
        if not b: raise ValueError("Unexpected EOF in VINT")
        value = (value << 8) | b[0]
    return value, length

class EbmlElement:
    def __init__(self, eid, payload=None, children=None):
        self.eid = eid
        self.payload = payload if payload is not None else b''
        self.children = children if children is not None else []
    
    def get_content_size(self):
        if self.children:
            return sum(c.total_size() for c in self.children)
        return len(self.payload)

    def total_size(self):
        id_len = 1
        if self.eid > 0xFFFFFF: id_len=4
        elif self.eid > 0xFFFF: id_len=3
        elif self.eid > 0xFF: id_len=2
        
        content_len = self.get_content_size()
        size_len = len(encode_vint(content_len))
        return id_len + size_len + content_len
        
    def write(self, stream):
        # ID
        if self.eid > 0xFFFFFF: stream.write(self.eid.to_bytes(4, 'big'))
        elif self.eid > 0xFFFF: stream.write(self.eid.to_bytes(3, 'big'))
        elif self.eid > 0xFF: stream.write(self.eid.to_bytes(2, 'big'))
        else: stream.write(self.eid.to_bytes(1, 'big'))
        
        # Size
        stream.write(encode_vint(self.get_content_size()))
        
        # Content
        if self.children:
            for child in self.children:
                child.write(stream)
        else:
            stream.write(self.payload)

def parse_ebml_stream(stream, size=None):
    elements = []
    start_pos = stream.tell()
    
    while True:
        if size is not None and (stream.tell() - start_pos) >= size:
            break
            
        # Peek ID
        pos_before = stream.tell()
        first = stream.read(1)
        if not first: break
        val = first[0]
        id_len = 1
        if val & 0x80: id_len = 1
        elif val & 0x40: id_len = 2
        elif val & 0x20: id_len = 3
        elif val & 0x10: id_len = 4
        else: 
            # Invalid ID or 0 padding?
            # Just consume 1 byte and continue?
            continue
            
        stream.seek(pos_before)
        eid_bytes = stream.read(id_len)
        eid = int.from_bytes(eid_bytes, 'big')
        
        content_size, vs = read_vint(stream)
        if content_size is None: break
        
        # Decide if container or leaf
        # Containers we care about: Segment, Tracks, TrackEntry, Video, Cluster, BlockGroup, BlockAdditions, BlockMore
        # Note: SeekHead, Info, Tags etc we treat as leaf payload for simplicity unless we need to descend
        
        containers = [
            EBML_ID_SEGMENT, EBML_ID_TRACKS, EBML_ID_TRACKENTRY, 
            EBML_ID_VIDEO, EBML_ID_CLUSTER, EBML_ID_BLOCKGROUP,
            EBML_ID_BLOCKADDITIONS, EBML_ID_BLOCKMORE
        ]
        
        if eid in containers:
            children = parse_ebml_stream(stream, content_size)
            elements.append(EbmlElement(eid, children=children))
        else:
            payload = stream.read(content_size)
            elements.append(EbmlElement(eid, payload=payload))
            
    return elements

def extract_alpha_frames(alpha_elements):
    frames = []
    
    def traverse(el):
        if el.eid == EBML_ID_SIMPLEBLOCK:
            # Parse SimpleBlock
            # TrackNum(Vint), Timecode(2), Flags(1), Frame...
            s = BytesIO(el.payload)
            read_vint(s) # Skip TrackNum
            s.read(3) # Skip Timecode, Flags
            frame_data = s.read()
            frames.append(frame_data)
        elif el.eid == EBML_ID_BLOCKGROUP:
            # Check Block
            for child in el.children:
                if child.eid == EBML_ID_BLOCK:
                    s = BytesIO(child.payload)
                    read_vint(s)
                    s.read(3)
                    frames.append(s.read())
        
        if el.children:
            for c in el.children:
                traverse(c)
                
    for e in alpha_elements:
        traverse(e)
        
    return frames

EBML_ID_TIMECODE = 0xE7
EBML_ID_REFERENCEBLOCK = 0xFB

def inject_alpha_into_color(color_elements, alpha_frames):
    
    alpha_ptr = 0
    # Track the absolute timecode of the PREVIOUS frame encountered
    last_absolute_timecode = 0
    
    # helper to read integer from bytes
    def read_uint(data):
        return int.from_bytes(data, 'big')

    def traverse_modify(el):
        nonlocal alpha_ptr
        nonlocal last_absolute_timecode
        
        if el.eid == EBML_ID_SEGMENT:
             # Filter out SeekHead, Cues, Void, Tags from Segment children
             el.children = [c for c in el.children if c.eid not in (EBML_ID_SEEKHEAD, EBML_ID_CUES, EBML_ID_VOID, EBML_ID_TAGS)]

        # 1. Modify Tracks -> TrackEntry -> Video to add AlphaMode
        if el.eid == EBML_ID_VIDEO:
            # Check if AlphaMode exists
            has_alpha = False
            for c in el.children:
                if c.eid == EBML_ID_ALPHAMODE: has_alpha = True
            
            if not has_alpha:
                el.children.append(EbmlElement(EBML_ID_ALPHAMODE, payload=(1).to_bytes(1, 'big')))
        
        # 2. Modify Cluster -> SimpleBlock to BlockGroup
        if el.eid == EBML_ID_CLUSTER:
            # Get Cluster Timecode
            cluster_timecode = 0
            for c in el.children:
                if c.eid == EBML_ID_TIMECODE:
                    cluster_timecode = read_uint(c.payload)
                    break
            
            new_children = []
            for c in el.children:
                if c.eid == EBML_ID_SIMPLEBLOCK:
                    # Convert to BlockGroup
                    if alpha_ptr >= len(alpha_frames):
                        # print("Warning: Not enough alpha frames")
                        new_children.append(c) 
                        continue
                        
                    alpha_data = alpha_frames[alpha_ptr]
                    alpha_ptr += 1
                    
                    # Parse SimpleBlock
                    sb = BytesIO(c.payload)
                    tn_val, tn_len = read_vint(sb)
                    
                    # Timecode (int16 signed)
                    tc_bytes = sb.read(2)
                    timecode_val = int.from_bytes(tc_bytes, 'big', signed=True) # it is signed int16 relative to cluster
                    
                    flags_byte = sb.read(1)
                    flags = flags_byte[0]
                    frame_data = sb.read()
                    
                    current_absolute_timecode = cluster_timecode + timecode_val
                    
                    # Construct Block Payload
                    blk_stream = BytesIO()
                    blk_stream.write(encode_vint(tn_val))
                    blk_stream.write(tc_bytes)
                    
                    # Check Keyframe
                    is_keyframe = (flags & 0x80) == 0x80
                    
                    clean_flags = flags & 0x7F # Mask off 0x80
                    blk_stream.write(clean_flags.to_bytes(1, 'big'))
                    
                    blk_stream.write(frame_data)
                    
                    block_elem = EbmlElement(EBML_ID_BLOCK, payload=blk_stream.getvalue())
                    
                    # BlockAdditions
                    block_add_id = EbmlElement(EBML_ID_BLOCKADDID, payload=(1).to_bytes(1, 'big'))
                    block_addition = EbmlElement(EBML_ID_BLOCKADDITIONAL, payload=alpha_data)
                    
                    block_more = EbmlElement(EBML_ID_BLOCKMORE, children=[block_add_id, block_addition])
                    block_additions = EbmlElement(EBML_ID_BLOCKADDITIONS, children=[block_more])
                    
                    block_group_children = [block_elem, block_additions]
                    
                    # Add ReferenceBlock if NOT keyframe
                    if not is_keyframe:
                        # Reference is relative to the current block's timecode
                        # e.g. ref_time = last_time
                        # offset = ref_time - current_time
                        # This should be negative.
                        offset = last_absolute_timecode - current_absolute_timecode
                        
                        # ReferenceBlock is Signed Integer (VINT-encoded? No, usually standard signed integer element, but wait...)
                        # Spec: "ReferenceBlock... Signed Integer". 
                        # In EBML, Signed Integer is variable length.
                        # We need to encode a signed integer. My EbmlElement writes raw payload.
                        # I need a helper for signed integer to bytes.
                        def int_to_sbytes(n):
                            length = (n.bit_length() + 8) // 8
                            if length == 0: length = 1
                            # For negative numbers, bit_length is of abs value? No.
                            # Just use to_bytes with signed=True and enough length
                            # -33 needs 1 byte (signed)
                            # -200 needs 2 bytes
                            try:
                                return n.to_bytes(length, 'big', signed=True)
                            except OverflowError:
                                return n.to_bytes(length+1, 'big', signed=True)

                        # We usually want minimal length
                        ref_payload = int_to_sbytes(offset)
                        block_group_children.append(EbmlElement(EBML_ID_REFERENCEBLOCK, payload=ref_payload))
                    
                    bg = EbmlElement(EBML_ID_BLOCKGROUP, children=block_group_children)
                    new_children.append(bg)
                    
                    # Update info
                    last_absolute_timecode = current_absolute_timecode

                else:
                    new_children.append(c)
            el.children = new_children

        # Recurse
        if el.children:
            for c in el.children:
                traverse_modify(c)

    traverse_modify(EbmlElement(0, children=color_elements)) # Dummy root wrapper to kickoff

def mux_files(color_path, alpha_path, output_path):
    print(f"Muxing {color_path} + {alpha_path} -> {output_path}")
    
    with open(color_path, 'rb') as f:
        color_elements = parse_ebml_stream(f)
        
    with open(alpha_path, 'rb') as f:
        alpha_elements = parse_ebml_stream(f)
        
    alpha_frames = extract_alpha_frames(alpha_elements)
    print(f"Extracted {len(alpha_frames)} alpha frames")
    
    inject_alpha_into_color(color_elements, alpha_frames)
    
    with open(output_path, 'wb') as f:
        for el in color_elements:
            el.write(f)
            
    print("Muxing complete.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 3:
        mux_files(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        # Default test
        if os.path.exists("test_color.webm") and os.path.exists("test_alpha.webm"):
            mux_files("test_color.webm", "test_alpha.webm", "test_muxed_alpha.webm")
