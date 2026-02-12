import re

from playwright.sync_api import Page, FrameLocator, Locator, expect


class GooglePayClient:
    """Адаптер для взаимодействия с окном/фреймом Google Pay.

    Отвечает за:
    - ожидание попапа/нового окна после выбора Google Pay;
    - логин в Google (email, пароль, backup-код 2FA);
    - подтверждение оплаты.

    Реальные локаторы могут отличаться, поэтому используются максимально
    общие и устойчивые паттерны по label/role/xpath, как в примерах Playwright.
    """

    def __init__(self, popup_page: Page) -> None:
        self.page = popup_page

    # -------------------- Вспомогательные методы --------------------
    def _email_input(self) -> Locator:
        # Gmail / Google login обычно имеет label "Email or phone" и id="identifierId".
        candidate = self.page.get_by_label(re.compile("Email|Phone", re.IGNORECASE))
        if candidate.count() > 0:
            return candidate.first

        candidate = self.page.locator("input#identifierId")
        if candidate.count() > 0:
            return candidate.first

        raise RuntimeError("Не удалось найти поле email на экране входа Google")

    def _password_input(self) -> Locator:
        candidate = self.page.get_by_label(re.compile("Password|Пароль", re.IGNORECASE))
        if candidate.count() > 0:
            return candidate.first

        candidate = self.page.locator("input[type='password']")
        if candidate.count() > 0:
            return candidate.first

        raise RuntimeError("Не удалось найти поле пароля Google")

    def _backup_code_input(self) -> Locator:
        # Экран резервного кода может иметь текст "Enter code" или аналогичный.
        candidate = self.page.get_by_role("textbox", name=re.compile("code|Код", re.IGNORECASE))
        if candidate.count() > 0:
            return candidate.first

        candidate = self.page.locator("input[type='tel']")
        if candidate.count() > 0:
            return candidate.first

        raise RuntimeError("Не удалось найти поле ввода backup-кода Google 2FA")

    def _next_button(self) -> Locator:
        return self.page.get_by_role(
            "button",
            name=re.compile("Next|Далее|Продолжить", re.IGNORECASE),
        )

    # -------------------- Основной flow Google login + оплата --------------------
    def login_and_confirm_payment(self, email: str, password: str, backup_code: str) -> None:
        """Выполняет полный сценарий: логин в Google и подтверждение оплаты.

        Предполагается, что self.page уже ссылается на попап/окно Google Pay,
        открытое после выбора способа оплаты на стороне Supercell.
        """

        # 1. Email / телефон
        email_input = self._email_input()
        email_input.fill(email)
        self._next_button().click()

        # 2. Пароль
        password_input = self._password_input()
        password_input.fill(password)
        self._next_button().click()

        # 3. Backup-код (2FA), если отображается соответствующий экран.
        try:
            backup_input = self._backup_code_input()
        except RuntimeError:
            backup_input = None

        if backup_input is not None:
            backup_input.fill(backup_code)
            self._next_button().click()

        # 4. Подтверждение оплаты (кнопка Pay/Оплатить).
        pay_button = self.page.get_by_role(
            "button",
            name=re.compile("Pay|Оплатить", re.IGNORECASE),
        )
        pay_button.click()

        # Ожидаем, что попап либо закроется, либо вернёт успешный статус.
        # Минимальная проверка: страница не содержит явного текста об ошибке.
        # В реальном проекте здесь можно добавить точные проверки по DOM.
        self.page.wait_for_load_state("networkidle")

        error_text = self.page.get_by_text(re.compile("error|ошибка|declined", re.IGNORECASE))
        if error_text.count() > 0:
            raise RuntimeError("Google Pay сообщает об ошибке при оплате")
