# Деплой на сервер (Ubuntu 22.04, VDS)

Инструкция для развёртывания Smart Holodilnik на арендованном VDS.
Ориентир: Ubuntu 22.04, 2 ГБ RAM, 2 ядра. Сервис занимает ~120 МБ RAM.

---

## 0. Подключение

```bash
ssh root@185.228.72.67
```

## 1. Безопасность (СНАЧАЛА это)

Пароль root, показанный в панели, считайте скомпрометированным.

```bash
# Сменить пароль root
passwd

# Создать отдельного пользователя с sudo (рекомендуется работать под ним)
adduser deploy
usermod -aG sudo deploy
```

**SSH-ключи вместо пароля** (выполнить НА СВОЁМ компьютере):

```bash
ssh-copy-id deploy@185.228.72.67
```

Затем на сервере отключить вход по паролю:

```bash
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

**Файрвол** — открыть только нужное:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp     # порт приложения (или 80/443, если поставите reverse proxy)
sudo ufw enable
```

## 2. Установка Docker

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # чтобы запускать docker без sudo
# перелогиньтесь (exit и снова ssh), чтобы группа применилась
```

## 3. Доставка кода

Вариант через git (если зальёте в репозиторий):

```bash
git clone <URL_вашего_репозитория> ~/holodilnik
cd ~/holodilnik
```

Либо скопировать папку проекта с компьютера:

```bash
# на своём компьютере, из родительской папки проекта
scp -r "26_06_15--Smart_Holodilnik" deploy@185.228.72.67:~/holodilnik
```

## 4. Конфигурация

```bash
cd ~/holodilnik
cp .env.example .env
nano .env
```

Заполнить при необходимости (всё опционально — без ключей сервис работает, AI-функции
покажут «не настроено»):

- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` — уведомления о сроках
- `OPENROUTER_API_KEY` — распознавание продуктов по фото
- `GROQ_API_KEY` — распознавание голоса
- `WARN_DAYS`, `DIGEST_HOUR` — настройки напоминаний

## 5. Запуск

```bash
docker compose up -d --build
```

Проверка:

```bash
docker compose ps
curl http://localhost:8000/health     # {"status":"ok"}
```

Открыть в браузере: `http://185.228.72.67:8000`

## 6. Эксплуатация

```bash
docker compose logs -f          # логи
docker compose restart          # перезапуск
docker compose down             # остановить
docker compose up -d --build    # обновить после изменения кода
```

База данных хранится в docker-томе `holodilnik_db` и переживает пересборку контейнера.

### Бэкап БД

```bash
docker compose cp holodilnik:/data/holodilnik.db ./holodilnik-backup-$(date +%F).db
```

---

## Опционально: HTTPS через Caddy

Если есть домен — проще всего Caddy (сам получает Let's Encrypt-сертификат).
Создать `Caddyfile`:

```
ваш-домен.ru {
    reverse_proxy localhost:8000
}
```

```bash
sudo apt install -y caddy
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl restart caddy
sudo ufw allow 443/tcp && sudo ufw allow 80/tcp
```

После этого закройте прямой порт приложения: `sudo ufw delete allow 8000/tcp`.
