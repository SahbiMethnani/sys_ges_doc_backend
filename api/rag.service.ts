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

// ------------------------------------------------------------------
// Service
// ------------------------------------------------------------------

@Injectable({ providedIn: 'root' })
export class RagService {
  private readonly apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  /** Statut du système RAG */
  getStatus(): Observable<StatusResponse> {
    return this.http.get<StatusResponse>(`${this.apiUrl}/status`);
  }

  /** Poser une question */
  query(question: string, showSources = true): Observable<QueryResponse> {
    const body: QueryRequest = { question, show_sources: showSources };
    return this.http.post<QueryResponse>(`${this.apiUrl}/query`, body);
  }

  /** Lister les documents indexés */
  listDocuments(): Observable<DocumentInfo[]> {
    return this.http.get<DocumentInfo[]>(`${this.apiUrl}/documents`);
  }

  /** Uploader un fichier */
  uploadDocument(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/documents/upload`, formData);
  }

  /** Réindexer les documents après upload */
  indexDocuments(): Observable<any> {
    return this.http.post(`${this.apiUrl}/documents/index`, {});
  }

  /** Supprimer un document */
  deleteDocument(filename: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/documents/${filename}`);
  }
}
