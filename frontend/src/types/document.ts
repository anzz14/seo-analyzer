export interface JobResponse {
	id: string;
	document_id: string;
	status: string;
	progress_percentage: number;
	current_stage: string;
	error_message: string | null;
	retry_count: number;
	created_at: string;
	started_at: string | null;
	completed_at: string | null;
}

export interface DocumentResponse {
	id: string;
	user_id: string;
	original_filename: string;
	file_size: number;
	mime_type: string;
	upload_timestamp: string;
	created_at: string;
	latest_job?: JobResponse;
}

export interface UploadResponse {
	document_id: string;
	job_id: string;
	filename: string;
	file_size: number;
}
