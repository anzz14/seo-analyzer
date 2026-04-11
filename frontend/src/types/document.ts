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
	latest_job?: JobResponse | null;
}

export interface KeywordMetric {
	keyword: string;
	count: number;
	density: number;
}

export interface ExtractedResultResponse {
	id: string;
	document_id: string;
	job_id: string;
	word_count: number | null;
	readability_score: number | null;
	primary_keywords: KeywordMetric[] | null;
	auto_summary: string | null;
	user_edited_summary: string | null;
	is_finalized: boolean;
	finalized_at: string | null;
	created_at: string;
}

export interface DocumentDetailResponse extends DocumentResponse {
	latest_job: JobResponse | null;
	result: ExtractedResultResponse | null;
}

export interface UploadResponse {
	document_id: string;
	job_id: string;
	filename: string;
	file_size: number;
}
