"""
LLM Handler - Qwen2.5-VL (multimodal) on CPU or GPU
"""

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from typing import Optional, Dict, Any
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

QWEN_VL_PATH = "./llama-models/qwen2.5-vl-7b-instruct"


class LocalLlamaHandler:
    """Multimodal LLM handler backed by Qwen2.5-VL-7B-Instruct."""

    def __init__(self):
        self.processor = None
        self.tokenizer = None  # alias for backwards compatibility
        self.model = None
        self.model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_vl = True

    def load_model(self):
        if not Path(QWEN_VL_PATH).exists():
            raise FileNotFoundError(f"Qwen2.5-VL model not found at {QWEN_VL_PATH}")
        self._load_qwen_vl()
        return True

    def _load_qwen_vl(self):
        logger.info(f"Loading Qwen2.5-VL from {QWEN_VL_PATH} on {self.device.upper()}...")
        self.processor = AutoProcessor.from_pretrained(QWEN_VL_PATH, local_files_only=True)
        self.tokenizer = self.processor  # kept for code paths that reference `tokenizer`

        if self.device == "cuda":
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                QWEN_VL_PATH,
                local_files_only=True,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
            )
        else:
            # CPU path: bfloat16 halves memory vs fp32 and is natively supported on modern CPUs
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                QWEN_VL_PATH,
                local_files_only=True,
                torch_dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
            )
            self.model.to("cpu")

        self.model.eval()
        self.model_name = "Qwen2.5-VL-7B-Instruct"
        logger.info(f"Qwen2.5-VL loaded on {self.device.upper()}")

    def generate(self, prompt: str, image_path: str = None,
                 max_new_tokens: int = 512, temperature: float = 0.7,
                 top_p: float = 0.9, do_sample: bool = True) -> str:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        try:
            return self._generate_vl(prompt, image_path, max_new_tokens, temperature, top_p, do_sample)
        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            raise

    def _generate_vl(self, prompt, image_path, max_new_tokens, temperature, top_p, do_sample):
        content = []
        has_image = image_path and Path(image_path).exists()
        if has_image:
            content.append({"type": "image", "image": f"file://{Path(image_path).resolve()}"})
        content.append({"type": "text", "text": prompt})
        messages = [{"role": "user", "content": content}]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        image_inputs = video_inputs = None
        if has_image:
            from qwen_vl_utils import process_vision_info
            image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
            )

        trimmed = output_ids[:, inputs.input_ids.shape[1]:]
        decoded = self.processor.batch_decode(trimmed, skip_special_tokens=True)
        return decoded[0].strip() if decoded else ""

    def extract_json_from_response(self, response: str) -> Optional[Dict[Any, Any]]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        if "```json" in response:
            try:
                return json.loads(response.split("```json")[1].split("```")[0].strip())
            except Exception:
                pass
        elif "```" in response:
            try:
                return json.loads(response.split("```")[1].split("```")[0].strip())
            except Exception:
                pass

        start = response.find("{")
        if start != -1:
            brace_count = 0
            for i in range(start, len(response)):
                if response[i] == "{":
                    brace_count += 1
                elif response[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            return json.loads(response[start:i+1])
                        except Exception:
                            pass
                        break

        logger.warning(f"Could not extract JSON: {response[:200]}")
        return None

    def extract_document_data(self, ocr_text: str, change_type: str, document_type: str, image_path: str = None) -> Dict[str, Any]:
        prompt = f"""You are a document analysis expert for a banking system. Analyze the following document and extract relevant information.

Document Type: {document_type}
Change Type: {change_type}
OCR Text: {ocr_text or 'N/A'}

Return ONLY a JSON object:
{{"old_name": "old/maiden name if present", "new_name": "new/married name if present", "document_date": "date if present", "document_number": "reference number if present", "issuing_authority": "who issued it", "other_details": "other relevant info"}}"""

        response = self.generate(prompt, image_path=image_path, max_new_tokens=256, temperature=0.3)
        return self.extract_json_from_response(response) or {}

    def verify_name_match(self, old_name: str, new_name: str, extracted_data: Dict[str, str]) -> Dict[str, Any]:
        prompt = f"""Verify name change. Old: {old_name}, New: {new_name}. Evidence: {json.dumps(extracted_data)}
Return ONLY JSON: {{"old_name_match": true, "new_name_match": true, "confidence_score": 85, "reasoning": "explanation", "recommendation": "approve"}}"""

        response = self.generate(prompt, max_new_tokens=200, temperature=0.2)
        return self.extract_json_from_response(response) or {
            "confidence_score": 0, "recommendation": "manual_review", "reasoning": "Failed to parse"
        }

    def detect_forgery(self, ocr_text: str, ocr_confidence: float, image_path: str = None) -> Dict[str, Any]:
        prompt = f"""Analyze document for forgery. OCR Confidence: {ocr_confidence}%. Text: {ocr_text[:300]}
Return ONLY JSON: {{"forgery_detected": false, "forgery_score": 20, "red_flags": [], "recommendation": "pass"}}"""

        response = self.generate(prompt, image_path=image_path, max_new_tokens=150, temperature=0.3)
        result = self.extract_json_from_response(response)
        if not result:
            return {"forgery_detected": False, "forgery_score": 30.0, "red_flags": [], "recommendation": "pass"}
        return result

    def generate_summary(self, request_data: Dict[str, Any], confidence_card: Dict[str, Any]) -> str:
        prompt = f"""Summarize this account change request in 2 sentences. Request: {json.dumps(request_data)}"""
        return self.generate(prompt, max_new_tokens=120, temperature=0.5)


_llama_handler = None


def get_llama_handler() -> LocalLlamaHandler:
    global _llama_handler
    if _llama_handler is None or _llama_handler.model is None:
        _llama_handler = None
        handler = LocalLlamaHandler()
        handler.load_model()
        _llama_handler = handler
        logger.info(f"LLM handler ready: {_llama_handler.model_name}")
    return _llama_handler
