# 🚀 autopip

**نصب‌کننده‌ی هوشمند کتابخانه‌های پایتون**

**دیگه لازم نیست دنبال خطای ModuleNotFoundError بدوی!  
لیب autopip خودش همه‌ی وابستگی‌ها رو پیدا و نصب می‌کنه ✨**

## ✨ چرا autopip؟
- 🔍 **تشخیص خودکار** ایمپورت‌ها از سورس‌کد
- 🧠**نگاشت هوشمند ماژول**→ پکیج (مثلاً cv2 → opencv-python)
- ✅ **نصب خودکار requirements.txt** در صورت وجود 
- 🤫**حالت silent** بدون اسپم اضافی
- 🎨 **خروجی رنگی و مرحله‌ای** برای تجربه‌ی کاربری بهتر
- 📝 **لاگ‌گیری ساده** برای بررسی بعدی
  


## ⚡ نصب سریع
```bash 
pip install pyautopip
```

## 🎯 استفاده
اجرای مستقیم به عنوان ماژول:
```bash
import autopip
import requests
import numpy as np
```
## وقتی اجرا کنی خروجیش میشه این:

```
🔎 Libraries detected:
- requests
- numpy

📦 Installing missing libraries...
✔ requests installed
✔ numpy installed

✅ All libraries are ready!
```
## توجه⚠️: حتما باید قبل از همه کتابخانه ها و در لاین1 ایمپورت شه تا درست کار کنه 

# 🛠 امکانات CLI
**- اجرای روی فایل خاص:**
```bash
  autopip myscript.py
```
**- حالت silent:**
```bash
  autopip myscript.py --silent
```
**- لاگ‌ها داخل فایل autopip.log ذخیره می‌شن.**

# 📜 مجوز
این پروژه تحت مجوز **MIT** منتشر شده.



# ❤️ سازنده
**FrameworkPython – با عشق برای جامعه‌ی پایتون**
