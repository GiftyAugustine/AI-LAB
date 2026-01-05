import torch
from PIL import Image
import io
import traceback  # Added for debugging

HAS_VLM_LIBS = False
IMPORT_ERROR = ""

try:
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info
    HAS_VLM_LIBS = True
except ImportError as e:
    HAS_VLM_LIBS = False
    IMPORT_ERROR = str(e)
    print(f"CRITICAL WARNING: VLM libraries failed to import. Cause: {e}")
except Exception as e:
    HAS_VLM_LIBS = False
    IMPORT_ERROR = str(e)
    print(f"CRITICAL WARNING: Unexpected error importing VLM libraries. Cause: {e}")

class QwenVLAnalyzer:
    def __init__(self, model_id: str = "Qwen/Qwen2-VL-2B-Instruct"):
        self.model = None
        self.processor = None
        self.model_id = model_id
        self.mock_mode = not HAS_VLM_LIBS

    def load_model(self):
        if self.mock_mode:
            print(f"Skipping model load. Mock Mode is active. Import Error was: {IMPORT_ERROR}")
            return

        print(f"Loading VLM Model: {self.model_id}...")
        try:
            # Force CPU usage if MPS is hitting memory limits
            device_map = "cpu"
            print(f"Initializing model with device_map='{device_map}' to save memory...")

            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_id,
                torch_dtype=torch.float32,
                device_map=device_map,
                attn_implementation="eager",
                trust_remote_code=True
            ).to("cpu")
            
            self.processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
            print("Model loaded successfully on CPU.")
            
        except Exception as e:
            print(f"Failed to load model: {e}")
            traceback.print_exc()
            print("Falling back to Mock Mode.")
            self.mock_mode = True

    def analyze(self, image_bytes: bytes) -> list[str]:
        """
        Analyzes the image and returns a list of ingredients.
        """
        if self.model is None and not self.mock_mode:
            self.load_model()
            
        if self.mock_mode:
            # Mock response for testing/demo without GPU
            # Returns a generic set of ingredients often found in kitchen images
            print("Processing in Mock Mode (Real AI is NOT running)...")
            return ["chicken", "onion", "garlic", "tomato", "rice"]

        # Real VLM Inference
        try:
            print("Received image for analysis...")
            image = Image.open(io.BytesIO(image_bytes))
            
            # Optimization: Resize huge images to speed up CPU inference
            # Qwen2-VL supports any res, but smaller = faster tokens
            print(f"Original image size: {image.size}")
            image.thumbnail((512, 512))
            print(f"Resized image for speed: {image.size}")
            
            # Qwen2-VL specific prompting
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image,
                        },
                        {"type": "text", "text": "List the visible food ingredients in this image as a comma-separated list. Output ONLY the items, nothing else."},
                    ],
                }
            ]

            # Prepare inputs
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            inputs = inputs.to(self.model.device)

            # Generate
            generated_ids = self.model.generate(**inputs, max_new_tokens=128)
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            print(f"VLM Output: {output_text}")
            
            # Parse CSV string to list
            # Clean up potential extra text
            cleaned = output_text.replace('.', '').replace('\n', ',')
            ingredients = [x.strip().lower() for x in cleaned.split(',') if x.strip()]
            
            return ingredients

        except Exception as e:
            print(f"Error during VLM inference: {e}")
            traceback.print_exc()
            return ["error_during_analysis"]

if __name__ == "__main__":
    analyzer = QwenVLAnalyzer()
    # Test with mock or real
    print(analyzer.analyze(b"fake_image_bytes"))
