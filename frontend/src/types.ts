export interface AppUser {
  id: string;
  email: string;
}

export interface UploadRecord {
  id: string;
  created_at: string;
  denial_filename: string | null;
  medical_filename: string | null;
  denial_category: string | null;
  insurer_name?: string | null;
  confidence_score?: number | null;
  status: "processed" | "pending" | "error";
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
  created_at: string;
}

export interface TemplateOption {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface GenerateLetterRequest {
  case_id: string;
  template_id: string;
  format: "pdf" | "docx" | "txt";
}
