# Image URL Guide for iGlobals Books

## How to Get Book Cover Images

### Option 1: Unsplash (Recommended - Free)
Unsplash provides high-quality, free-to-use images.

**Steps:**
1. Go to [unsplash.com](https://unsplash.com)
2. Search for relevant terms:
   - "textbook"
   - "education"
   - "study"
   - "books"
   - "science textbook"
   - "mathematics"
   - etc.
3. Click on an image you like
4. Right-click on the image and select "Copy image address"
5. The URL format should be: `https://images.unsplash.com/photo-XXXXX?w=600&q=80`

**Tips:**
- Add `?w=600&q=80` to the end of the URL for optimized size
- Use portrait-oriented images (taller than wide) for best results
- Search for specific subjects (e.g., "chemistry lab", "literature books")

### Option 2: Pexels (Free Alternative)
Similar to Unsplash, Pexels offers free stock photos.

**Steps:**
1. Go to [pexels.com](https://www.pexels.com)
2. Search for book-related images
3. Click on an image
4. Right-click and copy the image URL
5. Use the medium or large size URL

### Option 3: Custom Book Covers
If you have custom book cover designs:

**Using Imgur:**
1. Go to [imgur.com](https://imgur.com)
2. Click "New post"
3. Upload your book cover image
4. After upload, right-click the image and copy the direct link
5. Use the `.jpg` or `.png` direct link

**Using Cloudinary (Professional):**
1. Sign up at [cloudinary.com](https://cloudinary.com) (free tier available)
2. Upload your images
3. Copy the generated URL
4. Format: `https://res.cloudinary.com/YOUR_CLOUD_NAME/image/upload/v1234567890/book_cover.jpg`

### Option 4: Google Drive (For Team Sharing)
1. Upload image to Google Drive
2. Right-click → Get link → Change to "Anyone with the link"
3. Copy the file ID from the URL
4. Use format: `https://drive.google.com/uc?export=view&id=FILE_ID`

## Image Specifications

### Recommended Dimensions:
- **Width**: 400-600px
- **Height**: 600-900px
- **Aspect Ratio**: 2:3 (portrait)
- **Format**: JPG or PNG
- **File Size**: Under 500KB for fast loading

### Image Quality:
- **Resolution**: 72-150 DPI (for web)
- **Color Mode**: RGB
- **Compression**: Medium to High (balance quality and size)

## Example URLs for Different Subjects

### Science Books:
```
https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=600&q=80  # Lab equipment
https://images.unsplash.com/photo-1636466497217-26a8cbeaf0aa?w=600&q=80  # Physics
https://images.unsplash.com/photo-1530973428-5bf2db2e4d71?w=600&q=80  # Biology
https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?w=600&q=80  # Chemistry
```

### Arts & Humanities:
```
https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&q=80  # Literature
https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=600&q=80  # Government
https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600&q=80  # Books
```

### Commercial/Business:
```
https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&q=80  # Accounting
https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&q=80  # Business
https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600&q=80  # Economics
```

## Adding Images to Books

### Via Admin Panel:
1. Log in to admin panel
2. Go to Books → Edit Book
3. Paste the image URL in the "Image URL" field
4. Save changes

### Via Seed Data:
```python
{
    'title': 'Book Title',
    'author': 'Author Name',
    'image_url': 'https://images.unsplash.com/photo-XXXXX?w=600&q=80',
    # ... other fields
}
```

## Troubleshooting

### Image Not Showing:
1. **Check URL**: Make sure it's a direct image link (ends with .jpg, .png, or has image parameters)
2. **Test URL**: Open the URL in a new browser tab to verify it loads
3. **HTTPS**: Ensure the URL uses `https://` not `http://`
4. **Permissions**: For Google Drive/Dropbox, ensure sharing is set to "Anyone with link"

### Image Too Large/Small:
1. **Unsplash**: Add `?w=600&q=80` to resize
2. **Cloudinary**: Use transformation parameters: `/w_600,h_900,c_fill/`
3. **Imgur**: Use the medium size link

### Image Wrong Aspect Ratio:
- The system uses `aspect-ratio: 2/3` and `object-fit: cover`
- Images will be cropped to fit
- Use portrait-oriented images for best results

## Best Practices

1. **Consistency**: Use images from the same source for a cohesive look
2. **Quality**: Choose high-resolution images that look professional
3. **Relevance**: Select images that relate to the book's subject
4. **Copyright**: Only use images you have rights to or from free stock sites
5. **Performance**: Optimize images before uploading (compress, resize)
6. **Backup**: Keep a copy of all book cover images in a dedicated folder

## Quick Reference

| Source | Free | Quality | Ease of Use | Best For |
|--------|------|---------|-------------|----------|
| Unsplash | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Stock photos |
| Pexels | ✅ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Stock photos |
| Imgur | ✅ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Custom uploads |
| Cloudinary | ✅/💰 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Professional hosting |
| Google Drive | ✅ | ⭐⭐⭐ | ⭐⭐ | Team sharing |

## Need Help?

If you're having trouble with images:
1. Check the browser console for errors (F12)
2. Verify the URL loads in a new tab
3. Try a different image source
4. Contact support with the book ID and error message


<img src="https://i.ibb.co/fVNFxGM3/iglobals-business-121230-jpg.jpg" alt="iglobals business 121230 jpg" border="0">
<img src="https://i.ibb.co/N2DK8cZb/iglobals-crs-120738-jpg.jpg" alt="iglobals crs 120738 jpg" border="0">
<img src="https://i.ibb.co/YFJzjp9N/IGLOBALS-ECONOMICS-120709-jpg.jpg" alt="IGLOBALS ECONOMICS 120709 jpg" border="0">
<img src="https://i.ibb.co/4nZPp9gg/iglobals-econs-commercial-121219-jpg.jpg" alt="iglobals econs commercial 121219 jpg" border="0">
<img src="https://i.ibb.co/YF7Z23vy/IGLOBALS-GOVERNMENT-120727-jpg.jpg" alt="IGLOBALS GOVERNMENT 120727 jpg" border="0">
<img src="https://i.ibb.co/KcDk1GzP/iglobals-physics-044503-jpg.jpg" alt="iglobals physics 044503 jpg" border="0">
<img src="https://i.ibb.co/Jjvwg5V0/iglobals-chemistry-044512-jpg.jpg" alt="iglobals chemistry 044512 jpg" border="0">
<img src="https://i.ibb.co/9H3g6RtK/iglobals-gov-coomercial-121237-jpg.jpg" alt="iglobals gov coomercial 121237 jpg" border="0">
<img src="https://i.ibb.co/fdsX2sPH/iglobals-accounting-121210-jpg.jpg" alt="iglobals accounting 121210 jpg" border="0">
<img src="https://i.ibb.co/Q3cSHg1C/iglobals-lit-in-eng-120719-jpg.jpg" alt="iglobals lit in eng 120719 jpg" border="0">
<img src="https://i.ibb.co/RGWHftZk/IGLOBALS-MATHS-044519-jpg.jpg" alt="IGLOBALS MATHS 044519 jpg" border="0">
<img src="https://i.ibb.co/3yZnJYGm/iglobals-biology-044443-jpg.jpg" alt="iglobals biology 044443 jpg" border="0">