# نصب و راه‌اندازی JavaidPanel

**نسخه سورس:** 1.1.111-dev · **وضعیت:** نصب آزمایشی؛ تست کامل VPS انجام نشده است.

## ۱. آماده‌سازی سرور

برای نخستین نصب، یک VPS تازه با Ubuntu 24.04 یا Debian 12/13، معماری `x86_64`، systemd فعال و دسترسی sudo در نظر بگیرید. قبل از اجرا، بکاپ و امکان بازیابی سرور داشته باشید. نصب‌کننده دسترسی root می‌خواهد و فایل‌ها و سرویس‌های سیستمی ایجاد می‌کند.

حداقل سخت‌افزار مورد بررسی در اسکریپت: حدود 512 MiB RAM و 2 GiB فضای آزاد در `/opt`؛ **این ارقام تضمین کفایت منابع برای استفاده عملیاتی نیستند.**

**نکته حیاتی:** برای نصب تعاملی حتماً ترمینال کنترل‌کننده (TTY) داشته باشید تا انتخاب دامنه و SSL پرسیده شود. نصب بدون ترمینال و بدون تعیین `ALIREZA_TLS_MODE` اکنون با خطا متوقف می‌شود. برای کار غیرتعاملی، باید mode و host را عمداً تنظیم کنید؛ استفاده از متغیرهای محیطی حاوی رمز را در history یا log ننویسید.

## ۲. بررسی بدون نصب

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | bash -s -- --doctor
```

نتیجهٔ این دستور فقط قابلیت‌های اولیه VPS را نشان می‌دهد و تغییری در سیستم نمی‌دهد.

## ۳. نصب با یک دستور

پس از بازبینی محتوای اسکریپت و روی VPS آزمایشی:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
```

بوت‌استرپ فایل `installer/core.sh` همین مخزن را دریافت می‌کند، SHA-256 آن را با مقدار پین‌شده مقایسه می‌کند و موتور نصب را اجرا می‌کند. در صورت عدم تطابق هش، کار متوقف می‌شود.

### روش قابل بازرسی

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash -n install.sh
bash install.sh --self-test
sudo bash install.sh --doctor
sudo bash install.sh
```

## ۴. دامنه و SSL

در مسیر نصب پایه، انتخاب نوع دسترسی، دامنه و روش TLS وجود دارد. برای Let's Encrypt باید مالک دامنه باشید، DNS درست باشد و روش ACME در فایروال قابل دسترس باشد.

برای مدیریت SSL بعد از نصب:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --ssl
```

**هشدار:** این نسخه هنوز ویزارد وب اختصاصی برای تعیین دامنه، ساخت مدیر و صدور گواهی خودکار ندارد. دریافت گواهی در محیط واقعی نیز هنوز آزمایش نشده است. [راهنمای SSL](SSL.md).

## ۵. تأیید سرویس

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --check
```

بعد از نصب باید لاگ سرویس‌ها، پاسخ HTTP(S)، گواهی، ورود مدیر و اتصال آزمایشی را **به‌صورت واقعی** بررسی کنید. صرف چاپ «موفق» در ترمینال کافی نیست.

## ۶. نودها

نودهای پایه با دستور جداگانه فعال می‌شوند:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --enable-nodes
```

این گزینه، عامل اختصاصی جدید Javid Node را نصب نمی‌کند. [راهنمای نودها](NODES.md) و [طرح اتصال نود](NODE_ENROLLMENT.md) را بخوانید.

## ۷. به‌روزرسانی و بازیابی

قبل از هر تغییر، از داده‌ها و تنظیمات سرور نسخه پشتیبان بگیرید. مسیر تعمیر پایه:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash -s -- --repair
```

این دستور **جایگزین بکاپ و rollback تست‌شده نیست**. در صورت خطا، وضعیت سرویس‌ها و لاگ‌ها را ذخیره و از [راهنمای رفع خطا](TROUBLESHOOTING.md) استفاده کنید.

## وضعیت سازگاری

| محیط | وضعیت |
|---|---|
| Ubuntu 24.04 + x86_64 + systemd | مورد پذیرش کد؛ تست VPS لازم |
| Debian 12 / 13 + x86_64 + systemd | مورد پذیرش کد؛ تست VPS لازم |
| سایر نسخه‌ها و arm64 | در نصب‌کنندهٔ جاری تأیید نشده |
| Docker Compose مستقل | طرح ناقص قبلی بایگانی و از ریشه پروژه حذف شده؛ نصب کانتینری پشتیبانی نشده |

راهنما: [معماری](ARCHITECTURE.md) · [ماتریس امکانات](FEATURES.md) · [SSL](SSL.md)

### محدودیت نصب فعلی

`install.sh` فقط Gateway و هسته پایه را نصب می‌کند؛ API و عامل مستقل **Javid Node** با آن نصب نمی‌شوند. [ممیزی امکانات فعلی](CURRENT_FEATURES_AUDIT.md).

## ۸. تست خواندنی بعد از نصب

پس از نصب آزمایشی، `sudo python3 tools/vps-postinstall-smoke.py --run` را از مخزن اجرا کنید؛ این دستور فایل‌های خصوصی را افشا یا سرویس‌ها را تغییر نمی‌دهد. آزمون ورود مدیر، TLS بیرونی، VPN واقعی و backup/restore باید جداگانه انجام شود. [راهنمای تست](VPS_SMOKE_TEST.md).
