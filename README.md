<div align="center">

# JavaidPanel · جاوید پنل

**مدیریت زیرساخت VPN و اتصال نودهای مستقل**

![Version](https://img.shields.io/badge/version-1.1.107--dev-f04452?style=for-the-badge)
![Status](https://img.shields.io/badge/status-development-f6b35e?style=for-the-badge)
![CI](https://github.com/wisealii/JavaidPanel/actions/workflows/verify.yml/badge.svg)

[**مستندات**](docs/index.html) · [**دمو**](docs/demo.html) · [**اتصال نود و داشبورد مدیریتی**](docs/NODE_DASHBOARD.md) · [**API نودها**](docs/JAVID_NODE_API.md) · [**راهنمای آسان SSL**](docs/SSL_QUICKSTART.md) · [**وضعیت امکانات**](docs/FEATURES.md)

</div>

---

## درباره JavaidPanel

JavaidPanel پروژهٔ مدیریت VPN، سرورها و نودهای چندسروری با هویت مستقل JP UI است. در نسخهٔ **1.1.107-dev** یک سرویس مستقل API برای ایجاد نود، صدور توکن ثبت یک‌بارمصرف، عامل گزارش سلامت و ابطال نود اضافه شده است.

**تفاوت مهم:** اتصال API و عامل سلامت نود اکنون قابل اجرا و دارای تست آفلاین است، ولی هنوز به داشبورد اصلی پنل وصل نیست و موتور VPN یا تونل روی نود راه‌اندازی نمی‌کند. تأیید اتصال واقعی دو VPS و استقرار نهایی باقی مانده است.

## قابلیت‌های فعلی

| قابلیت | وضعیت |
|---|---|
| نصب یک‌دستوری هسته پایه | پیاده‌سازی و آزمایش ایستا، VPS هنوز تست نشده |
| مدیریت دامنه و گواهی | هسته پایه و **ویزارد ترمینالی گام‌به‌گام SSL** |
| ساخت نود و توکن کوتاه‌عمر | **API عملیاتی در محیط آزمایشی** |
| ثبت یک‌بارمصرف و جلوگیری از Replay | پیاده‌سازی و تست آفلاین |
| عامل Javid Node و heartbeat امضاشده | کد و سرویس systemd، تست شبکه محلی |
| تشخیص آنلاین/آفلاین با heartbeat واقعی | پیاده‌سازی و تست آفلاین |
| اتصال API به رابط فعلی پنل | هنوز ادغام نشده |
| ساخت تونل/VPN روی VPS نود | هنوز پیاده‌سازی نشده |
| نصب و SSL روی VPS واقعی | هنوز تأیید نشده |

## نصب آزمایشی هسته پایه

فقط روی **VPS تازه آزمایشی** با Ubuntu 24.04 یا Debian 12/13، x86_64 و systemd:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | sudo bash
```

برای بررسی بدون نصب:

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/install.sh | bash -s -- --doctor
```

[راهنمای نصب کامل](docs/INSTALLATION.md)

## SSL در پنج مرحله ساده

1. دامنه را به IP سرور متصل کنید.
2. پورت TCP 80 را برای اعتبارسنجی HTTP-01 بررسی کنید.
3. Certbot را نصب کنید.
4. راهنمای تعاملی را اجرا کنید.
5. گواهی را به وب‌سرور پنل وصل و HTTPS را تست کنید.

```bash
sudo bash tools/ssl-wizard.sh
```

**مهم:** گرفتن گواهی به‌تنهایی HTTPS پنل را فعال نمی‌کند. [راهنمای تصویری و مرحله‌ای](docs/SSL_QUICKSTART.md)

## Javid Node: API و عامل واقعی (آزمایشی)

از کپی سورس روی سرور مرکزی:

```bash
sudo bash tools/install-control-plane.sh --install
curl http://127.0.0.1:9443/healthz
```

سرویس ابتدا فقط روی **127.0.0.1** بالا می‌آید. قبل از اتصال VPS دوم باید یک reverse proxy با **HTTPS معتبر** برای API تنظیم شود.

از روی سرور مرکزی، پس از تنظیم HTTPS عمومی:

```bash
sudo python3 tools/javidctl.py \
  --config /etc/javid-panel/node-control.json \
  create --name 'Germany-01' --host 203.0.113.24 \
  --panel https://panel.example.org
```

این فرمان **توکن یک‌بارمصرف و دستور نصب مختص نود** ارائه می‌کند. توکن در دستور نصب قرار نمی‌گیرد؛ فقط یک بار با ورودی مخفی روی سرور نود وارد می‌شود.

[تمام مراحل، روش تست و endpointها](docs/JAVID_NODE_API.md)

## تست سورس

```bash
python3 -m unittest discover -s tests -p 'test_node_api.py' -v
python3 -m unittest discover -s tests -p 'test_ssl_wizard.py' -v
```

## معماری و مجوزها

کدهای عمومی، اسکریپت‌ها، ماژول‌ها و تغییرات با مجوزهای موجود در [LICENSE](LICENSE) و [SOURCES.md](SOURCES.md) منتشر شده‌اند. از این پروژه به‌عنوان محصول مستقل JavaidPanel نام برده می‌شود؛ اما اعلان‌های حقوقی وابستگی‌های متن‌باز حفظ می‌شوند.

[وضعیت کامل](docs/STATUS.md) · [نقشه توسعه](docs/ROADMAP.md) · [راهنمای مشارکت](CONTRIBUTING.md)

**توجه:** هیچ پروتکل، SSL، یا تونل تست‌نشده‌ای به‌عنوان قابلیت پایدار معرفی نمی‌شود.

## داشبورد واقعی «اتصال نود» (آزمایشی)

برای مدیریت نودها، یک صفحه **واقعی** روی همان API کنترلر اضافه شده است. این صفحه با دادهٔ زندهٔ API کار می‌کند و مانند دموی عمومی JavaidPanel ساختگی نیست. برای جلوگیری از دسترسی عمومی، فقط از طریق SSH Tunnel باز شود:

```bash
ssh -L 9443:127.0.0.1:9443 USER@CONTROL_VPS
```

در مرورگر دستگاه خودتان: `http://127.0.0.1:9443/admin/nodes`

ساخت نود و دریافت اسکریپت/توکن مستقل، مشاهده آخرین heartbeat و ابطال دسترسی در همین صفحه انجام می‌شود. **این داشبورد درگاه مدیریتی مستقل کنترلر است و هنوز داخل Gateway اصلی پنل ادغام نشده؛ استقرار روی دو VPS تست نشده است.** [راهنمای مرحله‌به‌مرحله](docs/NODE_DASHBOARD.md).

## ارتقای کنترلر بدون از دست‌دادن داده‌ها

از این نسخه یک ابزار جداگانه برای ارتقای **سورس Javid Node Controller** اضافه شده است. این ابزار دیتابیس، توکن‌ها و فایل تنظیمات خصوصی را جایگزین نمی‌کند؛ پیش از راه‌اندازی نسخه جدید، سورس قبلی را نگه می‌دارد و در صورت خطای Restart یا Health Check، تلاش می‌کند خودکار آن را برگرداند.

```bash
python3 tools/upgrade-control-plane.py --plan
sudo python3 tools/upgrade-control-plane.py --apply
```

**حتماً پیش از اجرا راهنما را بخوانید:** [مراحل ارتقای امن و بازیابی](docs/NODE_UPGRADE.md). این یک ارتقای آزمایشی کنترلر است؛ نه ارتقای Gateway اصلی و نه نسخهٔ تأییدشده برای سرور عملیاتی.
