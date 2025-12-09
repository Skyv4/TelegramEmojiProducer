const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ConversionResult {
    id: string;
    original_filename?: string;
    original_url?: string;
    converted_filename?: string; // The converted filename from the backend
    original_size: number;
    converted_size: number;
    compression_ratio: number;
    download_url?: string;
    status: 'pending' | 'completed' | 'failed' | 'admin_completed';
    error?: string;
}

export interface BatchConversionResponse {
    results: ConversionResult[];
}

export interface StatsResponse {
    total_conversions: number;
    available_downloads: number;
    total_output_size: number;
    total_output_size_mb: number;
}

export async function convertFile(file: File): Promise<ConversionResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/convert`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Conversion failed');
    }

    return await response.json();
}

export async function convertUrl(url: string): Promise<ConversionResult> {
    const response = await fetch(`${API_BASE_URL}/api/convert-url?url=${encodeURIComponent(url)}`, {
        method: 'POST',
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'URL conversion failed');
    }

    return await response.json();
}

export async function convertBatch(files: File[]): Promise<BatchConversionResponse> {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/api/convert-batch`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Batch conversion failed');
    }

    return response.json();
}

export function getDownloadUrl(filename: string): string {
    return `${API_BASE_URL}/api/download/${filename}`;
}

export async function getStats(): Promise<StatsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/stats`);

    if (!response.ok) {
        throw new Error('Failed to fetch stats');
    }

    return response.json();
}

// Admin API calls
const ADMIN_USERNAME = "admin"; // Hardcoded for now
const ADMIN_PASSWORD = "hamilton jacobi bellman"; // Keep this secure in a real app!

async function adminFetch(path: string, options?: RequestInit): Promise<Response> {
    const headers = new Headers(options?.headers);
    headers.set('Authorization', 'Basic ' + btoa(ADMIN_USERNAME + ':' + ADMIN_PASSWORD));

    return fetch(`${API_BASE_URL}${path}`, { ...options, headers });
}

export async function getAllConversionRequests(): Promise<ConversionResult[]> {
    const response = await adminFetch('/api/admin/requests');
    if (!response.ok) {
        throw new Error('Failed to fetch conversion requests');
    }
    const data = await response.json();
    return data.requests;
}

export async function completeConversionRequest(requestId: string): Promise<void> {
    const response = await adminFetch(`/api/admin/requests/${requestId}/complete`, {
        method: 'POST',
    });
    if (!response.ok) {
        throw new Error(`Failed to complete request ${requestId}`);
    }
}

export async function getConversionRequest(requestId: string): Promise<ConversionResult> {
    const response = await adminFetch(`/api/admin/requests/${requestId}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch request ${requestId}`);
    }
    return await response.json();
}
