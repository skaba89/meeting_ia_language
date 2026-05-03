/**
 * API proxy route: forwards all /api/* requests to the FastAPI backend.
 * Uses Next.js server-side fetching to bypass the Caddy gateway namespace issue.
 *
 * Frontend calls /api/auth/login → proxy → http://localhost:8000/auth/login
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[]
) {
  const path = pathSegments.join("/");
  const url = `${BACKEND_URL}/${path}`;

  // Forward query parameters (excluding XTransformPort)
  const searchParams = new URLSearchParams(request.nextUrl.searchParams);
  searchParams.delete("XTransformPort");
  const queryString = searchParams.toString();
  const fullUrl = queryString ? `${url}?${queryString}` : url;

  // Forward headers — keep content-type with boundary for multipart
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    // Skip hop-by-hop headers that shouldn't be forwarded
    if (lower === "host" || lower === "connection" || lower === "transfer-encoding") return;
    headers.set(key, value);
  });

  // Build fetch options
  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: "follow",
  };

  // Forward body for non-GET requests
  if (request.method !== "GET" && request.method !== "HEAD") {
    // Forward raw body as-is, preserving multipart boundaries
    init.body = await request.arrayBuffer();
  }

  try {
    const response = await fetch(fullUrl, init);

    // Build response headers
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      responseHeaders.set(key, value);
    });

    const body = await response.arrayBuffer();
    return new NextResponse(body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error(`[API Proxy] Error forwarding to ${fullUrl}:`, error.message);
    return NextResponse.json(
      { detail: `Backend unavailable: ${error.message}` },
      { status: 502 }
    );
  }
}
