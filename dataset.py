from torch.utils.data import Dataset
from torchvision import transforms
from data.db import get_image_data
from data.collection import collect, get_next_images, get_skipped
from config import images_path
from PIL import Image
import pandas as pd
from PIL import Image
import os, warnings, asyncio


warnings.filterwarnings(
    "ignore",
    message="Palette images with Transparency expressed in bytes"
)

class HorseyDataset(Dataset):
    def __init__(self, image_path, input_csv, size=224):
        self.df_horsies = pd.read_csv(input_csv)
        self.img_path = image_path
        self.size = size
        self.t = transforms.Compose([
            transforms.RandomResizedCrop(size),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(0.2, 0.2, 0.2, 0.2),
            transforms.ToTensor()
        ])

    
    def __len__(self):
        return len(self.df_horsies)

    def __getitem__(self, index):
        metadata = self.df_horsies.iloc[index]
        img_path = f"{self.img_path}/{metadata['id']}.{metadata['format']}"

        with Image.open(img_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img = self.t(img)
        
        return img


def get_present_images():
    present = os.listdir(images_path)

    return pd.DataFrame({
        'id': map(lambda file_name: int(file_name[:file_name.index('.')]), present)
    })



def clean_images(df: pd.DataFrame):
    path = images_path

    for i, (img_id, _, img_format, _, _) in enumerate(df.itertuples(index=False), 1):
        img_path = path / f'{img_id}.{img_format}'

        print(f'{i * 100 / (len(df)):.3f}{' '*10}', end='\r')

        try:
            with Image.open(img_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    img.save(img_path, optimize=True)

        except Exception as e:
            print(f'Skipping: {img_path} {e}')

if __name__ == '__main__':
    df = get_present_images()
    df = get_image_data(df)

    print(f'Collected: {len(df)}')

    # to_collect = get_next_images(df, 'filtered', 10000)
    # to_collect = get_skipped(df, 206400 - len(df))
    # to_collect = get_image_data(pd.DataFrame({ 'id': [] }))

    # asyncio.run(collect(to_collect, images_path, lambda: 0.3))

    #asyncio.run(collect(redo, images_path, lambda: 0))

    #broken = [481684]

    df = df.sort_values('id')
    df['tags'] = df['tags'].apply(lambda tags: '|'.join(tags))
    df.to_csv('data/image_data.csv', index=False)
    print('Done')
