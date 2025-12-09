"use client";

import { useState, useCallback } from 'react';
import { Upload, FileVideo, Sparkles, CheckCircle, AlertCircle, Download, Loader2 } from 'lucide-react';
import { convertFile, convertUrl, getDownloadUrl, type ConversionResult as ApiConversionResult } from '@/lib/api';

export default function Home() {
    const [files, setFiles] = useState<File[]>([]);
    const [url, setUrl] = useState<string>("");
    const [isDragging, setIsDragging] = useState(false);
    const [isConverting, setIsConverting] = useState(false);
    const [results, setResults] = useState<ApiConversionResult[]>([]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFiles = Array.from(e.dataTransfer.files).filter(
            file => file.type.startsWith('image/gif') || file.type.startsWith('video/')
        );

        setFiles(prev => [...prev, ...droppedFiles]);
    }, []);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const selectedFiles = Array.from(e.target.files);
            setFiles(prev => [...prev, ...selectedFiles]);
        }
    }, []);

    const removeFile = useCallback((index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    }, []);

    const handleConvert = async () => {
        if (files.length === 0) return;

        setIsConverting(true);
        setResults([]);

        try {
            const newResults: ApiConversionResult[] = [];
            for (const file of files) {
                try {
                    const result = await convertFile(file);
                    newResults.push(result);
                } catch (error: any) {
                    console.error("Error converting file:", file.name, error);
                    newResults.push({
                        id: `error-${file.name}`,
                        original_filename: file.name,
                        original_size: file.size,
                        converted_size: 0,
                        compression_ratio: 0,
                        status: 'failed',
                        error: error.message || 'Unknown error',
                    });
                }
            }
            setResults(newResults);
        } catch (batchError: any) {
            console.error("Error during batch conversion:", batchError);
            alert(`An error occurred during conversion: ${batchError.message}`);
        } finally {
            setIsConverting(false);
        }
    };

    const handleUrlChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        setUrl(e.target.value);
    }, []);

    const handleUrlConvert = async () => {
        if (!url) {
            alert("Please enter a URL first!");
            return;
        }

        setIsConverting(true);
        setResults([]);

        try {
            const result = await convertUrl(url);
            setResults([result]);
        } catch (error: any) {
            console.error("Error converting URL:", error);
            alert(`An error occurred during URL conversion: ${error.message}`);
            setResults([{ 
                id: `error-${url}`,
                original_url: url,
                original_size: 0,
                converted_size: 0,
                compression_ratio: 0,
                status: 'failed',
                error: error.message || 'Unknown error',
            }]);
        } finally {
            setIsConverting(false);
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    return (
        <div className="min-h-screen relative overflow-hidden">
            {/* Animated Background */}
            <div className="fixed inset-0 -z-10">
                <div className="absolute inset-0 gradient-mesh opacity-30"></div>
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-600/20 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-600/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
            </div>

            {/* Header */}
            <header className="relative z-10 pt-8 pb-4">
                <div className="container mx-auto px-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl gradient-primary flex items-center justify-center shadow-lg">
                                <Sparkles className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-gradient">Telegram Sticker Converter</h1>
                                <p className="text-sm text-gray-400">Transform media into perfect stickers</p>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                <div className="max-w-4xl mx-auto space-y-8">

                    {/* Hero Section */}
                    <div className="text-center space-y-4 animate-slide-in-down">
                        <h2 className="text-4xl md:text-5xl font-bold">
                            Create <span className="text-gradient">Perfect</span> Telegram Stickers
                        </h2>
                        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                            Convert GIFs and videos to Telegram-compliant WebM stickers with transparency,
                            optimized size, and perfect quality.
                        </p>
                    </div>

                    {/* Features */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-slide-in-up">
                        <div className="card-glass text-center p-6">
                            <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center mx-auto mb-3">
                                <CheckCircle className="w-6 h-6 text-primary-400" />
                            </div>
                            <h3 className="font-semibold mb-2">Auto-Optimized</h3>
                            <p className="text-sm text-gray-400">Automatically resized to 512px and under 64KB</p>
                        </div>

                        <div className="card-glass text-center p-6">
                            <div className="w-12 h-12 rounded-xl bg-accent-500/20 flex items-center justify-center mx-auto mb-3">
                                <Sparkles className="w-6 h-6 text-accent-400" />
                            </div>
                            <h3 className="font-semibold mb-2">Transparency Support</h3>
                            <p className="text-sm text-gray-400">Preserves alpha channel for transparent backgrounds</p>
                        </div>

                        <div className="card-glass text-center p-6">
                            <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center mx-auto mb-3">
                                <FileVideo className="w-6 h-6 text-green-400" />
                            </div>
                            <h3 className="font-semibold mb-2">Perfect Duration</h3>
                            <p className="text-sm text-gray-400">Trimmed to 2.84 seconds for Telegram compliance</p>
                        </div>
                    </div>

                    {/* Upload Area */}
                    <div className="card-elevated animate-slide-in-up" style={{ animationDelay: '0.1s' }}>
                        <div
                            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${isDragging
                                ? 'border-primary-500 bg-primary-500/10'
                                : 'border-white/20 hover:border-white/30'
                                }`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                        >
                            <input
                                type="file"
                                id="file-upload"
                                className="hidden"
                                multiple
                                accept="image/gif,video/*"
                                onChange={handleFileSelect}
                            />

                            <div className="space-y-4">
                                <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mx-auto shadow-glow">
                                    <Upload className="w-10 h-10 text-white" />
                                </div>

                                <div>
                                    <h3 className="text-xl font-semibold mb-2">Drop your files here</h3>
                                    <p className="text-gray-400 mb-4">or click to browse</p>

                                    <label htmlFor="file-upload" className="btn btn-primary cursor-pointer inline-block">
                                        <span>Choose Files</span>
                                    </label>
                                </div>

                                <p className="text-sm text-gray-500">
                                    Supports GIF and video files (MP4, MOV, AVI, etc.)
                                </p>
                            </div>
                        </div>

                        {/* URL Input */}
                        <div className="mt-6 space-y-3">
                            <h4 className="font-semibold">Or convert from URL</h4>
                            <input
                                type="text"
                                placeholder="Enter emoji URL (e.g., https://example.com/animated.gif)"
                                value={url}
                                onChange={handleUrlChange}
                                className="w-full p-3 rounded-xl bg-white/5 border border-white/10 focus:border-primary-500 focus:ring-primary-500 text-white"
                            />
                            <button
                                onClick={handleUrlConvert}
                                disabled={isConverting}
                                className="btn btn-secondary w-full"
                            >
                                {isConverting ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                        Converting URL...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="w-5 h-5 mr-2" />
                                        Convert URL to Sticker
                                    </>
                                )}
                            </button>
                        </div>

                        {/* File List */}
                        {files.length > 0 && (
                            <div className="mt-6 space-y-3">
                                <div className="flex items-center justify-between">
                                    <h4 className="font-semibold">Selected Files ({files.length})</h4>
                                    <button
                                        onClick={() => setFiles([])}
                                        className="text-sm text-gray-400 hover:text-white transition-colors"
                                    >
                                        Clear all
                                    </button>
                                </div>

                                <div className="space-y-2 max-h-64 overflow-y-auto">
                                    {files.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                                        >
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <FileVideo className="w-5 h-5 text-primary-400 flex-shrink-0" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-medium truncate">{file.name}</p>
                                                    <p className="text-sm text-gray-400">{formatFileSize(file.size)}</p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFile(index)}
                                                className="text-gray-400 hover:text-red-400 transition-colors ml-2"
                                            >
                                                ×
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                <button
                                    onClick={handleConvert}
                                    disabled={isConverting}
                                    className="btn btn-primary w-full"
                                >
                                    {isConverting ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                            Converting...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-5 h-5 mr-2" />
                                            Convert to Stickers
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Results */}
                    {results.length > 0 && (
                        <div className="card-elevated animate-slide-in-up space-y-4">
                            <h3 className="text-xl font-semibold flex items-center gap-2">
                                <CheckCircle className="w-6 h-6 text-green-400" />
                                Conversion Results
                            </h3>

                            <div className="space-y-3">
                                {results.map((result, index) => (
                                    <div
                                        key={index}
                                        className="p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-2">
                                                    {result.status === 'completed' ? (
                                                        <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                                                    ) : (
                                                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                                                    )}
                                                    <p className="font-medium truncate">{result.original_filename || result.original_url}</p>
                                                </div>

                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                                    <div>
                                                        <p className="text-gray-400">Original</p>
                                                        <p className="font-medium">{formatFileSize(result.original_size)}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Converted</p>
                                                        <p className="font-medium text-green-400">{formatFileSize(result.converted_size)}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Saved</p>
                                                        <p className="font-medium text-primary-400">
                                                            {result.original_size > 0 ? ((1 - result.converted_size / result.original_size) * 100).toFixed(0) : 0}%
                                                        </p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-400">Status</p>
                                                        <p className="font-medium capitalize">{result.status.replace('_', ' ')}</p>
                                                    </div>
                                                </div>
                                            </div>

                                            {result.status === 'completed' && result.download_url && (
                                                <a
                                                    href={getDownloadUrl(result.converted_filename!)}
                                                    className="btn btn-secondary flex items-center gap-2 flex-shrink-0"
                                                    download
                                                >
                                                    <Download className="w-4 h-4" />
                                                    Download
                                                </a>
                                            )}
                                            {result.status === 'failed' && result.error && (
                                                <p className="text-red-400 text-sm">Error: {result.error}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Info Section */}
                    <div className="card-glass animate-slide-in-up" style={{ animationDelay: '0.2s' }}>
                        <h3 className="text-lg font-semibold mb-4">Telegram Sticker Requirements</h3>
                        <div className="grid md:grid-cols-2 gap-4 text-sm">
                            <div className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-medium">Format</p>
                                    <p className="text-gray-400">WebM with VP9 codec and alpha channel</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-medium">Dimensions</p>
                                    <p className="text-gray-400">512px on the longest side</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-medium">Duration</p>
                                    <p className="text-gray-400">Maximum 3 seconds (optimized to 2.84s)</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="font-medium">File Size</p>
                                    <p className="text-gray-400">Under 64KB for optimal performance</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* Footer */}
            <footer className="relative z-10 py-8 mt-16">
                <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
                    <p>Built with ❤️ for Telegram sticker creators</p>
                </div>
            </footer>
        </div>
    );
}
