# نصب یک‌دستوری JavaidPanel — 1.1.103-dev

## یک دستور برای نصب آزمایشی

روی VPS **تازه**، با **Ubuntu 24.04 یا Debian 12/13**، `x86_64` و `systemd`:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
```

این دستور فایل `installer/core.sh` را دانلود می‌کند، SHA-256 آن را با هش پین‌شدهٔ `c24354d80b223023541c388a6d493be893660c6798e98e5d70725fcb18ab174c` تطبیق می‌دهد و سپس نصب‌کننده پایهٔ AlirezaPanel 2.8.0 را اجرا می‌کند. این نسخه VPN-UI v1.9.4 و AdGuard Home v0.107.79 را از انتشارهای اصلی با بررسی SHA-256 دریافت می‌کند.

### روش قابل بازبینی قبل از اجرا

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash -n install.sh
bash install.sh --self-test
sudo bash install.sh --doctor
sudo bash install.sh
```

### دامنه و SSL

در اجرای تعاملی، تنظیم نوع دسترسی (دامنه، IP ACME، IP خودامضا یا بدون TLS) توسط هسته پایه انجام می‌شود. اگر از خط لولهٔ `curl | sudo bash` استفاده می‌کنید، بوت‌استرپ سعی می‌کند ورودی را از ترمینال واقعی بخواند. امکان تعیین متغیرهای محیطی `ALIREZA_HOST`، `ALIREZA_TLS_MODE` و `ALIREZA_ACME_EMAIL` نیز وجود دارد.

برای نمونه، روی VPS آزمایشی با دامنه‌ای که به سرور اشاره می‌کند:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo env ALIREZA_TLS_MODE=domain ALIREZA_HOST=panel.example.org bash
```

متغیرهای محیطی تنها نمونه‌اند؛ دامنه باید واقعی باشد و پورت‌های ACME در دسترس باشند.

بعد از نصب، دستور زیر را برای ویزارد گواهی اجرا کنید:

```bash
sudo bash install.sh --ssl
```

## وضعیت پشتیبانی

- Ubuntu 24.04 / Debian 12/13، x86_64: **در سطح کد پذیرفته می‌شوند**؛ آزمون نصب زندهٔ ما انجام نشده است.
- Ubuntu 20.04 / 22.04 / 26.04: در حال حاضر به‌صورت پیش‌فرض رد می‌شوند.
- حداقل اعلام‌شده در نصب‌کنندهٔ پایه 512 MiB RAM و توصیه 1 GiB است؛ کفایت این اعداد برای بار واقعی تأیید نشده.

## نودها

مدیریت نود در هستهٔ پایه AlirezaPanel وجود دارد و فرمان `--enable-nodes` پس از نصب در دسترس است. اما **Javid Node** جدید به Gateway اصلی متصل نیست و ثبت امن چند VPS روی محیط واقعی آزمایش نشده است.

## خطرات و بازگشت

این نصب‌کننده بسته نصب می‌کند، فایل‌های `/opt/alirezapanel` و `/etc/alirezapanel` را ایجاد می‌کند و سرویس‌های systemd را راه‌اندازی می‌کند. روی سرور اصلی بدون بکاپ استفاده نکنید. از نصب روی VPS دارای AlirezaPanel پیشین جلوگیری می‌شود.

**مهم:** نصب یک‌دستوری آمادهٔ تست است، نه تضمین پایداری عملیاتی.
