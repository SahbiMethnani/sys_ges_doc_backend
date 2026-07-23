// rag.service.ts — Service Angular pour consommer l'API RAG
// Placez ce fichier dans src/app/services/

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

// ------------------------------------------------------------------
// Interfaces (miroir des modèles Pydantic côté FastAPI)
// ------------------------------------------------------------------

export interface QueryRequest {
  question: string;
  show_sources?: boolean;
}

export interface SourceDocument {
  source: string;
  content: string;
}

export interface QueryResponse {
  answer: string;
  sources?: SourceDocument[];
}

export interface StatusResponse {
  status: string;
  documents_loaded: boolean;
  vector_store_exists: boolean;
  total_documents: number;
}

export interface DocumentInfo {
  filename: string;
  size: number;
  type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  display_name?: string;
  email?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email?: string;
  display_name?: string;
  role: 'user' | 'admin';
}

// ------------------------------------------------------------------
// Service
// ------------------------------------------------------------------

@Injectable({ providedIn: 'root' })
export class RagService {
  private readonly apiUrl = 'http://localhost:8000';
  private accessToken: string | null = null;

  constructor(private http: HttpClient) {}

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  private authHeaders(): { Authorization?: string } {
    return this.accessToken
      ? { Authorization: `Bearer ${this.accessToken}` }
      : {};
  }

  login(username: string, password: string) {
    return this.http.post<TokenResponse>(`${this.apiUrl}/auth/login`, {
      username,
      password,
    });
  }

  register(body: RegisterRequest) {
    return this.http.post<UserResponse>(`${this.apiUrl}/auth/register`, body);
  }

  me() {
    return this.http.get<UserResponse>(`${this.apiUrl}/auth/me`, {
      headers: this.authHeaders(),
    });
  }

  /** Statut du système RAG */
  getStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>(`${this.apiUrl}/status`);
  }

  /** Poser une question */
  query(question: string, showSources = true): Observable<QueryResponse> {
    const body: QueryRequest = { question, show_sources: showSources };
    return this.http.post<QueryResponse>(`${this.apiUrl}/query`, body, {
      headers: this.authHeaders(),
    });
  }

  /** Lister les documents indexés */
  listDocuments(): Observable<DocumentInfo[]> {
    return this.http.get<DocumentInfo[]>(`${this.apiUrl}/documents`, {
      headers: this.authHeaders(),
    });
  }

  /** Uploader un fichier */
  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/documents/upload`, formData, {
      headers: this.authHeaders(),
    });
  }

  /** Réindexer les documents après upload */
  indexDocuments(): Observable<any> {
    return this.http.post(`${this.apiUrl}/documents/index`, {}, {
      headers: this.authHeaders(),
    });
  }

  /** Supprimer un document */
  deleteDocument(filename: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents/${filename}`, {
      headers: this.authHeaders(),
    });
  }
}
