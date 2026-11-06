# معماری JavaidPanel

## اجزای فعلی

```text
VPS مرکزی
  ├── install.sh            Bootstrap + OS checks + SHA-256
  ├── installer/core.sh     موتور پایه و اسکریپت‌های یکپارچه
  ├── systemd               سرویس‌های ایجادشده در نصب پایه
  ├── Gateway / VPN Core    وابسته به اجرا و آزمون واقعی
  └── docs/                 مستندات و دموی ایستا (جدا از Gateway)

VPS نود
  └── node-agent-install.sh بررسی اولیه؛ نصب عامل جدید هنوز مسدود
```

`docker-compose.production.yml` یک **پیکربندی پیشنهادی ناقص و مجزا** است؛ در مخزن کنونی Dockerfile و پیکربندی Nginx لازم برای اجرای آن موجود نیست. بنابراین `docker compose up` به‌عنوان روش نصب توصیه نمی‌شود.

## محدودهٔ ماژول‌های آینده

```text
Admin UI (هدف)
  ├── Setup & Certificates
  ├── Users, Plans, Tickets, RBAC
  ├── Protocol Registry & Adapters
  ├── Node Registry + Enrollment Tokens
  └── Tunnels + Health + Audit
          │ REST API / Auth
          ▼
Control Plane (هدف)
  ├── Persistence + Migrations
  ├── Secrets / Certificate Rotation
  ├── Node Trust + Heartbeats
  └── Jobs / Events / Rollback
          │ mutual authenticated channels
          ▼
Data Plane (هدف): Node Agents / VPN Engines / Tunnel Adapters
```

نام‌گذاری محصول و طراحی عمومی JavaidPanel مستقل است. در نسخه جاری، تعدادی از شناسه‌های داخلی نصب‌کنندهٔ پایه برای سازگاری نگه داشته شده‌اند. **تغییر آن‌ها بدون migration و تست می‌تواند باعث از دست رفتن داده یا قطع سرویس شود.**

## اصول ثابت

- **کنترلر ≠ عامل:** سطح دسترسی و اسرار آن‌ها جدا باشد.
- **UI ≠ daemon:** وجود کارت یا دکمه، معادل عملکرد واقعی نیست.
- **ادعا ≠ تست:** هر پروتکل و نود باید با آزمون اتصال/قطع و گزارش ترافیک ارزیابی شود.
- **ورودی کاربر ≠ shell:** هیچ IP، hostname یا شناسه نود بدون اعتبارسنجی در فرمان shell وارد نشود.
- **داده واقعی ≠ دمو:** نمونه‌های سایت هیچ اتصال زنده‌ای ندارند.

[نودها](NODES.md) · [امکانات](FEATURES.md) · [توسعه](DEVELOPMENT.md)
