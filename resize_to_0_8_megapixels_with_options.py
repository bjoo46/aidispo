import torch
from PIL import Image, ImageOps
import numpy as np

class ResizeMegapixelsWithOptions:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_megapixels": (["0.8", "0.9", "1.0"], {"default": "0.9"}),
                "resize_method": (["stretch", "keep_aspect_ratio"],),
                "resample_filter": (["LANCZOS", "NEAREST", "BILINEAR", "BICUBIC", "BOX", "HAMMING"],),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "INT",)
    RETURN_NAMES = ("resized_image", "width", "height",)
    FUNCTION = "resize_and_align"
    CATEGORY = "Utilities/Image"

    def resize_and_align(self, image, target_megapixels, resize_method, resample_filter):
        if image.shape[0] > 1:
            print("Warning: Resizing multiple images at once. Only the first image will be processed.")
        
        img_np = (image[0].cpu().numpy() * 255.0).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        resample = getattr(Image.Resampling, resample_filter.upper(), Image.Resampling.LANCZOS)

        current_pixels = img_pil.width * img_pil.height
        
        # 선택된 메가픽셀 값에 따라 목표 픽셀 수 설정
        target_pixels = float(target_megapixels) * 1000000

        if resize_method == "stretch":
            aspect_ratio = img_pil.width / img_pil.height
            if aspect_ratio > 1:
                new_width = int((target_pixels * aspect_ratio) ** 0.5)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = int((target_pixels / aspect_ratio) ** 0.5)
                new_width = int(new_height * aspect_ratio)
            
            resized_img_pil = img_pil.resize((new_width, new_height), resample=resample)

        elif resize_method == "keep_aspect_ratio":
            scale_factor = (target_pixels / current_pixels) ** 0.5
            new_width = int(img_pil.width * scale_factor)
            new_height = int(img_pil.height * scale_factor)

            resized_img_pil = img_pil.resize((new_width, new_height), resample=resample)

        # 16의 배수로 크기를 조정
        aligned_width = (resized_img_pil.width + 15) // 16 * 16
        aligned_height = (resized_img_pil.height + 15) // 16 * 16
        
        if aligned_width != resized_img_pil.width or aligned_height != resized_img_pil.height:
            resized_img_pil = resized_img_pil.resize((aligned_width, aligned_height), resample=resample)

        resized_img_np = np.array(resized_img_pil).astype(np.float32) / 255.0
        resized_img_tensor = torch.from_numpy(resized_img_np).unsqueeze(0)

        final_width = resized_img_pil.width
        final_height = resized_img_pil.height

        return (resized_img_tensor, final_width, final_height,)

# ComfyUI에 노드를 등록
NODE_CLASS_MAPPINGS = {
    "ResizeMegapixelsWithOptions": ResizeMegapixelsWithOptions
}