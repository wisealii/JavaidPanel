<div align="center">

# JavaidPanel

**پنل مدیریت VPN · نودها · سرورها · ابزارهای شبکه**

**JP UI — Black / Red / White**

![Version](https://img.shields.io/badge/version-1.1.103--dev-f04452?style=for-the-badge) ![Installer](https://img.shields.io/badge/installer-one--command-eeeeee?style=for-the-badge) ![Testing](https://img.shields.io/badge/VPS%20validation-pending-ffc36b?style=for-the-badge)

[مستندات](docs/index.html) · [راهنمای نصب](docs/INSTALLATION.md) · [وضعیت قابلیت‌ها](docs/STATUS.md) · [مجوز و منابع](SOURCES.md)

</div>

## نصب روی VPS با یک دستور

**برای VPS تازه با Ubuntu 24.04 یا Debian 12/13، معماری x86_64 و systemd:**

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
```

این دستور **یک بوت‌استرپ واقعی** است: نصب‌کننده یک‌فایلی و پین‌شدهٔ مبتنی بر **AlirezaPanel 2.8.0** را از همین مخزن می‌گیرد، هش SHA-256 را بررسی می‌کند و پس از تأیید، راه‌اندازی VPN-UI v1.9.4 و AdGuard Home v0.107.79 را اجرا می‌کند.

**نکات مهم:**
- نصب مستقیم روی VPS واقعی هنوز توسط ما آزمایش نشده است؛ ابتدا روی سرور آزمایشی و پس از مطالعه اسکریپت اجرا شود.
- این **هستهٔ عملیاتی پایه** است، نه نسخهٔ تکمیل‌شدهٔ Javid Node یا فروش و پشتیبانی؛ این ماژول‌های جدید هنوز به Gateway متصل نشده‌اند.
- برای حفظ سازگاری، مسیرهای سرویس داخلی همچنان `alirezapanel` هستند.
- نصب‌کننده روی Ubuntu 20.04/22.04/26.04 مجاز نیست تا پشتیبانی واقعی تأیید شود.
- برای SSL معتبر دامنه، DNS و امکان پاسخگویی به ACME ضروری است.
- پروژه از کد GPL-3.0-or-later مشتق شده و نام/مجوز بالادست در `LICENSE` و `SOURCES.md` حفظ شده است.

## پیش از نصب

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | bash -s -- --doctor
```

یا فایل‌های پروژه را کلون و قبل از اجرا بازبینی کن:

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash install.sh --self-test
sudo bash install.sh --doctor
sudo bash install.sh
```

## پس از نصب

```bash
sudo bash install.sh --check
sudo bash install.sh --ssl
```

فرمان `--ssl` ابزار مدیریت گواهی موجود در هستهٔ AlirezaPanel را پس از نصب راه می‌اندازد.

## محدودهٔ نسخهٔ آزمایشی

هستهٔ VPN-UI و رابط AdGuard Home از سورس/انتشار پین‌شدهٔ بالادست نصب می‌شوند؛ اجزای اختصاصی و تجاری جدید جاوید و عامل نود مستقل هنوز آمادهٔ بهره‌برداری نیستند. دیدن پیام پایان نصب به معنای تأیید اتصال VPN و همهٔ پروتکل‌ها نیست.

[راهنمای نصب و رفع اشکال](docs/INSTALLATION.md) · [مسیر توسعه](docs/INSTALL_UX.md) · [وضعیت واقعی](docs/STATUS.md)
