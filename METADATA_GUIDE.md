# 📝 Creating Video Metadata Files - Step by Step

## What is a Metadata File?

A metadata file tells YouTube what your video is about - the title, description, tags, etc.

It's a simple text file you create in **Notepad** alongside your video.

---

## 🎯 Step-by-Step Instructions

### Step 1: Find Your Video File

Let's say you have a video called: **my_vacation.mp4**

### Step 2: Open Notepad

- Press `Windows Key`
- Type "Notepad"
- Click on Notepad to open it

### Step 3: Copy This Template

```
TITLE: Write your video title here

DESCRIPTION: Write your description here.
You can use multiple lines.

Add more details if you want!

TAGS: tag1, tag2, tag3

PRIVACY: private

CATEGORY: 22

MADE_FOR_KIDS: no
```

### Step 4: Fill in Your Details

```
TITLE: My Amazing Vacation in Hawaii

DESCRIPTION: Join me on my incredible journey to Hawaii!
In this video, I'll show you the beautiful beaches,
amazing food, and fun activities.

Don't forget to subscribe for more travel videos!

TAGS: hawaii, vacation, travel, beach, vlog

PRIVACY: private

CATEGORY: 19

MADE_FOR_KIDS: no
```

### Step 5: Save the File

1. Click **File** → **Save As**
2. Navigate to the **same folder** as your video
3. Name it: **my_vacation_metadata.txt** (must match video name + _metadata.txt)
4. Click **Save**

### Step 6: Check Your Files

You should now have:
```
📄 my_vacation.mp4
📄 my_vacation_metadata.txt
```

### Step 7: Upload Both to ToUpload Folder

- Copy both files to your ToUpload folder
- The system will automatically use the metadata when uploading!

---

## ✏️ Field Explanations

### **TITLE:**
- What your video will be called on YouTube
- Keep it under 100 characters
- Make it catchy and descriptive

**Examples:**
```
TITLE: How to Bake Perfect Chocolate Chip Cookies
TITLE: Morning Yoga Routine for Beginners
TITLE: iPhone 15 Review - Is It Worth It?
```

### **DESCRIPTION:**
- Detailed information about your video
- Can be as long as you want (up to 5000 characters)
- You can use multiple lines (just keep typing!)
- Great place to add links, timestamps, and details

**Example:**
```
DESCRIPTION: In this tutorial, I'll teach you how to bake
the perfect chocolate chip cookies!

Timestamps:
0:00 - Introduction
1:30 - Ingredients
3:00 - Mixing
5:00 - Baking

Recipe: https://example.com/recipe
Subscribe for more cooking videos!
```

### **TAGS:**
- Keywords that help people find your video
- Separate with commas
- Use 5-15 relevant tags
- Think about what people might search for

**Examples:**
```
TAGS: cooking, baking, cookies, recipe, tutorial, easy
TAGS: yoga, fitness, morning routine, stretching, wellness
TAGS: tech, review, iphone, apple, smartphone
```

### **PRIVACY:**
- Controls who can see your video
- Three options:
  - `private` - Only you can see it
  - `unlisted` - Anyone with the link can see it
  - `public` - Everyone can find and watch it

**Examples:**
```
PRIVACY: private    (Start here, make public later)
PRIVACY: unlisted   (Share with specific people)
PRIVACY: public     (Available to everyone)
```

### **CATEGORY:**
- YouTube's content category
- Use the number from the list below
- Most common: 22 (People & Blogs)

**Common Categories:**
```
CATEGORY: 1   (Film & Animation)
CATEGORY: 10  (Music)
CATEGORY: 17  (Sports)
CATEGORY: 19  (Travel & Events)
CATEGORY: 20  (Gaming)
CATEGORY: 22  (People & Blogs) ← Most common
CATEGORY: 23  (Comedy)
CATEGORY: 24  (Entertainment)
CATEGORY: 26  (Howto & Style)
CATEGORY: 27  (Education)
CATEGORY: 28  (Science & Technology)
```

### **MADE_FOR_KIDS:**
- Required by YouTube (COPPA compliance)
- Is your video specifically for children under 13?
- Two options:
  - `yes` - Video is for kids
  - `no` - Video is NOT specifically for kids (most common)

**Examples:**
```
MADE_FOR_KIDS: no   (Most videos)
MADE_FOR_KIDS: yes  (Cartoons, nursery rhymes, kid content)
```

---

## 💡 Quick Tips

✅ **File Name Must Match:**
- Video: `my_video.mp4`
- Metadata: `my_video_metadata.txt` ✅
- NOT: `metadata.txt` ❌
- NOT: `my_video.txt` ❌

✅ **Use Notepad:**
- Not Microsoft Word
- Not WordPad
- Just plain Notepad

✅ **Keep It Simple:**
- You don't need to fill in every field
- Leave out any field to use default from config
- Just TITLE is usually enough!

✅ **Test It:**
- Start with `PRIVACY: private`
- Check the video on YouTube
- Change to public when ready

---

## 🌟 Minimum Example

**Don't want to fill everything? Here's the minimum:**

```
TITLE: My Video Title

DESCRIPTION: Short description of my video.

PRIVACY: private
```

**That's it!** All other fields will use defaults from config.json.

---

## ⚡ Super Quick Example

**Just want a title?**

```
TITLE: My Video Title
```

Everything else will use defaults!

---

## 🎓 Practice Exercise

Try creating a metadata file for a pretend video:

**Video:** cooking_tutorial.mp4

**Your Task:** Create `cooking_tutorial_metadata.txt` with:
- A catchy title
- A 2-3 line description
- 5 relevant tags
- Private privacy
- Category 26 (Howto & Style)

---

## ❓ Troubleshooting

**Q: My metadata isn't working**
- Check file name matches video name exactly
- Make sure it ends with `_metadata.txt`
- Make sure both files are in ToUpload folder

**Q: Can I edit the metadata after uploading?**
- Yes! Go to YouTube Studio
- Or: Create new metadata file and re-upload

**Q: What if I make a mistake?**
- No problem! Video uploads as private by default
- Fix the metadata file
- Re-upload or edit in YouTube Studio

---

**Need help? Check the full USER_GUIDE.md or contact support!**
