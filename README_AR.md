# Merdo Zone Downloader — دليل البناء والنشر (Windows x64)

هذا المستودع يحتوي **الكود المصدري** ومُجهِّز إصدار آلي. يجهّز ملفين للتوزيع:

- `Merdo_Zone_Downloader_v1.2_Portable_Win64.zip` (الأفضل للنشر: تشغيل أسرع وأسهل للصيانة)
- `Merdo_Zone_Downloader_v1.2_Win64.exe` (ملف واحد: يبدأ أبطأ لأنه يفك المكتبات مؤقتًا)

كلتا النسختين تضم Python runtime ومكتبات PySide6 وyt-dlp وyt-dlp-ejs وأدوات Deno وFFmpeg وFFprobe في الحزمة؛ **المستخدم الذي ينزل الإصدار لا يحتاج pip أو Python أو Deno أو FFmpeg**.

> مهم: يحتوي هذا ZIP على **ملفات المصدر والبناء** وليس EXE جاهزًا. يتطلب إنشاء EXE تشغيل البناء على Windows 64-bit، واتصالًا بالإنترنت وقت البناء لتنزيل مكتبات Python وأدوات الطرف الثالث، أو استعمال النسخ الموجودة محليًا.

## 1) طريقة سهلة — دبل كليك

1. فك الضغط وافتح مجلد `Merdo_Zone_Downloader_GitHub` في VS Code.
2. ضع أيقونة مشروعك الرسمية (اختياري) في `assets/merdo.ico`.
3. شغّل `build_windows.bat`.
4. سيُنشئ `.venv` ويثبت الاعتمادات **داخل بيئة البناء فقط**.
5. سينزّل نسخ Windows x64 من Deno وFFmpeg (LGPL static) من صفحات الإصدارات الرسمية في GitHub؛ حجم التنزيل كبير نسبيًا.
6. سيولّد إصدار Portable وإصدار OneFile داخل `release/` مع `SHA256SUMS.txt`.

**إذا كان تنزيل GitHub بطيئًا أو معطّلًا عندك:** بما أن Deno وFFmpeg موجودان عندك، شغّل بدلاً من ذلك:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release.ps1 -Mode both -UseInstalledTools
```

هذا يأخذ ملفات `deno.exe` و`ffmpeg.exe` و`ffprobe.exe` من مسارات PATH المحلية؛ **تأكد أن FFmpeg المثبت عندك بنية static ولا يحتاج DLL خارجية**، وأن لك الحق في إعادة توزيعه. يفضّل وضع نسخ رسمية موثوقة ومستقلة في `vendor/bin` بدلاً من ذلك إن أمكن.

## 2) أوامر بناء بديلة

افتح PowerShell داخل المجلد:

```powershell
# نسختان
.\scripts\build_release.ps1 -Mode both

# Portable فقط
.\scripts\build_release.ps1 -Mode portable

# OneFile فقط
.\scripts\build_release.ps1 -Mode onefile
```

عند تشغيل PowerShell بحظر السكربتات، استخدم:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_release.ps1 -Mode both
```

## 3) بنية المجلد بعد البناء

```text
Merdo_Zone_Downloader_GitHub/
├── app/
│   └── merdo_zone_downloader.py   # مصدر التطبيق
├── assets/
│   └── merdo.ico                  # اختياري: أيقونتك الرسمية
├── scripts/
│   ├── prepare_tools.ps1          # تجهيز أدوات Deno/FFmpeg
│   └── build_release.ps1          # إصدار نسختين تلقائيًا
├── vendor/bin/                   # يُنشأ داخله deno.exe/ffmpeg.exe/ffprobe.exe
├── .github/workflows/
│   └── build-windows.yml         # GitHub Actions
├── Merdo_Zone_Downloader.spec     # قواعد PyInstaller
├── requirements.txt
├── requirements-build.txt
├── .gitignore
├── README.md
├── README_AR.md
├── THIRD_PARTY_NOTICES.md
├── LICENSE
├── build_windows.bat
├── run_dev.bat
├── .venv/                       # لا ترفع إلى GitHub
├── dist/                        # لا ترفع إلى GitHub
├── build/                       # لا ترفع إلى GitHub
└── release/
    ├── Merdo_Zone_Downloader_v1.2_Portable_Win64.zip
    ├── Merdo_Zone_Downloader_v1.2_Win64.exe
    ├── THIRD_PARTY_NOTICES.md
    └── SHA256SUMS.txt
```

## 4) الرفع إلى GitHub

1. أنشئ مستودعًا فارغًا (بدون إنشاء README إضافي) باسم `merdo-zone-downloader` على GitHub.
2. نفّذ من داخل جذر المشروع (مع تبديل `YOUR_USERNAME`):

```powershell
git init
git add .
git commit -m "Initial Merdo Zone Downloader release project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/merdo-zone-downloader.git
git push -u origin main
```

المستودع سيُظهر الكود والملفات والوثائق فقط. ملفات التنفيذ الضخمة توضع تحت **Releases** لا ضمن Git history.

## 5) إنشاء Release على GitHub

### طريقة يدوية

من صفحة المستودع: Releases -> Draft a new release -> Tag `v1.2.0` -> أرفق الملفات من `release/`:

- Portable ZIP
- OneFile EXE
- SHA256SUMS.txt
- THIRD_PARTY_NOTICES.md، مع أي مواد ترخيص إضافية لازمة

### طريقة آلية من GitHub Actions

بعد دفع المصدر إلى GitHub، ادخل تبويب Actions -> Windows release -> Run workflow.
سيُبنى الإصدار على جهاز Windows عند GitHub ويرفع الملفات ضمن **Artifacts** للمعاينة.
ولنشر Release تلقائيًا، نفّذ:

```powershell
git tag v1.2.0
git push origin v1.2.0
```

التشغيل بالوسم `v1.2.0` سيحاول إنشاء Release وإرفاق ملفي التنزيل. يحتاج المستودع إلى سماح `GITHUB_TOKEN` بالكتابة إلى محتوى المستودع (المحدد في workflow) وقد تحتاج ضبط الإعدادات حسب سياسات المستودع.

## 6) زر تنزيل على موقع Merdo Zone

بعد إنشاء Release، استبدل `YOUR_USERNAME`:

```text
https://github.com/YOUR_USERNAME/merdo-zone-downloader/releases/latest/download/Merdo_Zone_Downloader_v1.2_Portable_Win64.zip
```

كود React/Next.js:

```jsx
<a
  href="https://github.com/YOUR_USERNAME/merdo-zone-downloader/releases/latest/download/Merdo_Zone_Downloader_v1.2_Portable_Win64.zip"
  target="_blank"
  rel="noopener noreferrer"
>
  Download for Windows
</a>
```

رابط `/latest/download/` يعتمد على تسمية الملفات تمامًا وعلى وجود Release منشور يعتبره GitHub أحدث إصدار. إذا غيرت اسم الملف في إصدار لاحق، حدث الرابط في موقعك.

## 7) مراجعات ضرورية قبل النشر

- جرّب **النسخة Portable ونسخة OneFile** على جهاز Windows 10/11 نظيف لا توجد عليه Python أو Deno أو FFmpeg.
- جرّب تنزيل ملف صغير ودمج الفيديو والصوت. لا يعني نجاح بناء EXE أن شبكتك تستطيع الاتصال بخوادم YouTube؛ مشكلة `googlevideo.com` مستقلة.
- للتشخيص، لا تفترض أن OneFile يعالج تحذير SmartScreen؛ الشهادات وتوقيع الكود أمر مستقل.
- تأكد من مواصفات FFmpeg والتراخيص الخاصة بـ PySide6/Qt وFFmpeg. قراءة `THIRD_PARTY_NOTICES.md` **ضرورية** قبل إعادة التوزيع، ولا تكتفي بنقل ملف notices دون تحقيق متطلبات تراخيص الأطراف الثالثة.
- أيقونة `assets/merdo.ico` اختيارية. لا يحتوي المشروع هنا على نسخة أصلية من شعارك؛ أضف أيقونتك أنت.
- الملف `.gitignore` يمنع رفع `.venv` وملفات `vendor/bin/*.exe` وملفات البناء، ليسحب GitHub Actions الأدوات من المصادر الرسمية أثناء البناء.

## 8) ملاحظة على النسخة 1.2

يستخدم التطبيق `find_tool()` و`enable_bundled_tools()` بدل الاعتماد على PATH فقط، ويحدد `ffmpeg_location` ومسار Deno عند تشغيله من EXE مجمّع. حزمة yt-dlp-ejs تُجمع مع كود Python ومواردها باستخدام `collect_all()` داخل spec.

هذا التجهيز تم فحص صياغة Python والملفات وبنية الأرشيف، **لكن لم يُختبر بناء Windows أو تنزيل YouTube فعليًا** داخل بيئة إنشاء الملفات الحالية.
