# نصب JavaidPanel روی VPS

**وضعیت:** راهنمای نصب آزمایشی؛ در این بازطراحی تست نصب روی VPS واقعی انجام نشده است.

## پیش‌نیازها
- VPS **آزمایشی** با SSH و دسترسی sudo
- بکاپ از تنظیمات و داده‌ها و امکان بازگردانی سرور
- بررسی نسخه سیستم‌عامل، معماری و وابستگی‌های درخواست‌شده در `install.sh`
- بررسی امنیتی Docker Compose، پورت‌های ورودی، TLS و متغیرهای محیطی

## دریافت و بازبینی

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
bash -n install.sh
bash -n node-agent-install.sh
less install.sh
less docker-compose.production.yml
```

### اجرای آزمایشی

پس از بررسی محتوا و فقط روی VPS تازه و غیرعملیاتی:

```bash
sudo bash install.sh
```

این نصب‌کننده می‌تواند سرویس‌ها، بسته‌های سیستم و تنظیمات شبکه را تغییر دهد. خروجی واقعی نصب را نگه دارید و خطاهای آن را گزارش کنید.

**هشدار سازگاری:** نسخه‌های Ubuntu/Debian ذکرشده در README قدیمی را بدون آزمایش مستقل، «تأییدشده» تلقی نکنید.

[صفحه معرفی](index.html) | [وضعیت فنی](STATUS.md)
