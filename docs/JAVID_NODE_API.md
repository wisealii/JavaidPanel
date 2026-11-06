# Javid Node API · مرحلهٔ آزمایشی قابل اجرا

این نسخه **API واقعی JSON، ذخیره‌سازی نودها، ثبت یک‌بارمصرف، عامل ارسال heartbeat و مدیریت وضعیت** دارد؛ اما هنوز داخل داشبورد اصلی JavaidPanel ادغام نشده است و موتور VPN یا تونل روی VPS نود نصب نمی‌کند. ارتباط نود با سرور از **TLS معتبر + HMAC-SHA256 امضاشده** استفاده می‌کند؛ **mTLS و صدور گواهی مستقل برای هر نود هنوز پیاده‌سازی نشده**.

## آماده‌سازی روی VPS کنترلر

نیازها: Python 3.10+، systemd، کاربر sudo، کپی سورس JavaidPanel روی سرور، و یک دامنه HTTPS معتبر برای ارتباط نودها.

```bash
git clone https://github.com/wisealii/JavaidPanel.git
cd JavaidPanel
sudo bash tools/install-control-plane.sh --install
curl http://127.0.0.1:9443/healthz
```

اسکریپت کاربر سیستمی `javidpanel` می‌سازد؛ پیکربندی و دیتابیس با دسترسی خصوصی در `/etc/javid-panel` قرار می‌گیرند. سرویس `javid-node-control.service` **فقط روی 127.0.0.1:9443** گوش می‌دهد و نیازی به بازکردن این پورت در فایروال عمومی نیست.

### اتصال HTTPS عمومی — مرحله ضروری

قبل از اجرای نود، یک Reverse Proxy با TLS معتبر روی دامنهٔ کنترلر پیکربندی کنید. مثال تنظیم **مسیرهای جدید در وب‌سرور موجود Nginx** (آن را پس از بررسی سایر vhostهای پنل خودتان اعمال کنید):

```nginx
# داخل server { listen 443 ssl; server_name panel.example.org; ... }
# مسیرهای مدیریتی فقط از CLI محلی اجرا شوند، نه اینترنت.
location = /api/v1/nodes { return 404; }
location = /api/v1/nodes/enrollments { return 404; }
location ~ ^/api/v1/nodes/[^/]+/revoke$ { return 404; }
location /api/v1/nodes/ {
    client_max_body_size 4k;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_pass http://127.0.0.1:9443;
    proxy_read_timeout 15s;
}
```

این قطعه **به‌تنهایی Nginx کامل نیست**. پیش از `nginx -t` و `systemctl reload nginx` از فایل پشتیبان بگیرید. این مسیرها نباید توسط پراکسی یا CDN به HTTP ناامن هدایت شوند. امکان اجرای API در TLS مستقیم با گزینه‌های `--cert` و `--key` نیز وجود دارد؛ این حالت نیازمند مدیریت امن دسترسی به private key و تمدید گواهی است.

## گرفتن SSL با راهنمای ساده

```bash
sudo bash tools/ssl-wizard.sh --check panel.example.org
sudo bash tools/ssl-wizard.sh --issue panel.example.org admin@example.org
sudo bash tools/ssl-wizard.sh --status panel.example.org
```

یا بدون آرگومان `sudo bash tools/ssl-wizard.sh` را اجرا کنید تا دامنه و ایمیل را مرحله‌به‌مرحله بپرسد. این ابزار فقط گواهی می‌گیرد، **HTTPS پنل یا Nginx را خودکار فعال نمی‌کند**. نحوه اتصال گواهی به وب‌سرور در [راهنمای SSL](SSL_QUICKSTART.md) آمده است.

## ساخت نود و دریافت دستور نصب اختصاصی

روی VPS کنترلر، بعد از فعال‌شدن سرویس و HTTPS عمومی:

```bash
sudo python3 tools/javidctl.py \
  --config /etc/javid-panel/node-control.json \
  create --name 'Germany-01' --host 203.0.113.24 \
  --panel https://panel.example.org
```

پاسخ شامل شناسه نود، یک توکن کوتاه‌عمر و **دستور نصب مخصوص آن نود** است. توکن را در URL، آرگومان خط فرمان یا Issue عمومی قرار ندهید. خروجی را با فرد غیرمجاز به اشتراک نگذارید.

### اجرای دستور روی VPS دوم

فرمان خروجی از مرحله قبل را روی VPS نود اجرا کنید (قالب آن):

```bash
curl -fsSL https://raw.githubusercontent.com/wisealii/JavaidPanel/main/node-agent-install.sh | \
  sudo bash -s -- --panel https://panel.example.org --enrollment-id ENROLLMENT_UUID
```

عامل از شما **توکن را مخفیانه** می‌خواهد، گواهی HTTPS دامنه را با زنجیره اعتماد سیستم بررسی می‌کند، سپس کلید اختصاصی دریافت کرده و آن را با دسترسی `0600` ذخیره می‌کند. بعد از ثبت موفق، سرویس `javid-node-agent` هر ۳۰ ثانیه heartbeat امضاشده می‌فرستد. وضعیت `online` فقط تا ۹۰ ثانیه پس از heartbeat معتبر باقی می‌ماند.

برای بررسی:

```bash
sudo python3 tools/javidctl.py --config /etc/javid-panel/node-control.json list
sudo systemctl status javid-node-control
# روی VPS نود:
sudo systemctl status javid-node-agent
```

برای ابطال دسترسی یک نود:

```bash
sudo python3 tools/javidctl.py --config /etc/javid-panel/node-control.json revoke NODE_UUID
```

## API endpoints

| Method | Endpoint | دسترسی | عملکرد |
|---|---|---|---|
| GET | `/healthz` | عمومی | سلامت ساده سرویس، نه سلامت VPN |
| GET | `/api/v1/nodes` | Bearer ادمین | فهرست نودها، زمان آخرین heartbeat |
| POST | `/api/v1/nodes/enrollments` | Bearer ادمین | توکن یک‌بارمصرف با TTL ۶۰ تا ۱۸۰۰ ثانیه |
| POST | `/api/v1/nodes/claim` | توکن کوتاه‌عمر | ثبت یک‌بارمصرف و دریافت کلید HMAC نود |
| POST | `/api/v1/nodes/{id}/heartbeat` | HMAC + timestamp + counter | تأیید سلامت، جلوگیری از replay |
| POST | `/api/v1/nodes/{id}/revoke` | Bearer ادمین | ابطال نود و کلید آن |

احراز هویت پنل اصلی و RBAC هنوز به این API متصل نشده‌اند؛ توکن ادمین فقط در config خصوصی است. برای محیط تولید باید audit ماندگار، rate limiting در Reverse Proxy، چرخش کلیدها، بکاپ، mTLS یا هویت سخت‌افزاری و تست دو VPS واقعی اضافه شوند.

## آزمایش توسعه‌دهنده بدون VPS

```bash
python3 -m unittest discover -s tests -p 'test_node_api.py' -v
python3 -m unittest discover -s tests -p 'test_ssl_wizard.py' -v
```

آزمون‌ها درخواست واقعی localhost را با API اجرا می‌کنند، ولی گواهی Let's Encrypt، وضعیت سیستم‌عامل VPS و نصب systemd را آزمایش نمی‌کنند.

## رابط مدیریتی نود (مرحله چهارم)

صفحهٔ `/admin/nodes` از داخل سرویس کنترلر ارائه می‌شود و با همین REST API کار می‌کند، نه اطلاعات نمونه. **هیچ‌گاه آن را در Reverse Proxy عمومی فعال نکنید.** از طریق SSH Tunnel و localhost باز کنید؛ ورود با توکن مدیریتی فقط در حافظهٔ مرورگر است. [راهنمای کامل](NODE_DASHBOARD.md).
