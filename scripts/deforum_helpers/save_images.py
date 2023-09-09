from typing import List, Tuple
from einops import rearrange
import numpy as np, os, torch
from PIL import Image
from torchvision.utils import make_grid
import time
from modules.shared import opts

DEBUG_MODE = opts.data.get("deforum_debug_mode_enabled", False)


def get_output_folder(output_path, batch_folder):
    out_path = os.path.join(output_path,time.strftime('%Y-%m'))
    if batch_folder != "":
        out_path = os.path.join(out_path, batch_folder)
    os.makedirs(out_path, exist_ok=True)
    return out_path


def save_samples(
    args, x_samples: torch.Tensor, seed: int, n_rows: int
) -> Tuple[Image.Image, List[Image.Image]]:
    """Function to save samples to disk.
    Args:
        args: Stable deforum diffusion arguments.
        x_samples: Samples to save.
        seed: Seed for the experiment.
        n_rows: Number of rows in the grid.
    Returns:
        A tuple of the grid image and a list of the generated images.
        ( grid_image, generated_images )
    """

    # save samples
    images = []
    grid_image = None
    if args.display_samples or args.save_samples:
        for index, x_sample in enumerate(x_samples):
            x_sample = 255.0 * rearrange(x_sample.cpu().numpy(), "c h w -> h w c")
            images.append(Image.fromarray(x_sample.astype(np.uint8)))
            if args.save_samples:
                images[-1].save(
                    os.path.join(
                        args.outdir, f"{args.timestring}_{index:02}_{seed}.png"
                    )
                )

    # save grid
    if args.display_grid or args.save_grid:
        grid = torch.stack([x_samples], 0)
        grid = rearrange(grid, "n b c h w -> (n b) c h w")
        grid = make_grid(grid, nrow=n_rows, padding=0)

        # to image
        grid = 255.0 * rearrange(grid, "c h w -> h w c").cpu().numpy()
        grid_image = Image.fromarray(grid.astype(np.uint8))
        if args.save_grid:
            grid_image.save(
                os.path.join(args.outdir, f"{args.timestring}_{seed}_grid.png")
            )

    # return grid_image and individual sample images
    return grid_image, images

def save_image(image, image_type, filename, args, video_args, root):
    if video_args.store_frames_in_ram:
        root.frames_cache.append({'path':os.path.join(args.outdir, filename), 'image':image, 'image_type':image_type})
    else:
        image.save(os.path.join(args.outdir, filename))

import cv2, gc

def reset_frames_cache(root):
    root.frames_cache = []
    gc.collect()

def dump_frames_cache(root):
    for image_cache in root.frames_cache:
        if image_cache['image_type'] == 'cv2':
            cv2.imwrite(image_cache['path'], image_cache['image'])
        elif image_cache['image_type'] == 'PIL':
            image_cache['image'].save(image_cache['path'])
    # do not reset the cache since we're going to add frame erasing later function #TODO 
