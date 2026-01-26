from typing import List
from src.domain.interfaces import MistakeCatalog
from src.domain.models import Mistake, Example


class ShortMistakeCatalog(MistakeCatalog):
    def list(self) -> List[Mistake]:
        return [
            Mistake(slug="Ad Hominem", description="Атака на личность вместо аргумента."),
            Mistake(slug="Straw Man", description="Искажение аргумента оппонента."),
            Mistake(slug="Complex Question", description="Многовопросие, подразумевает спорные посылки."),
            Mistake(slug="False Accusation of Lack of Evidence", description="Ложное обвинение в отсутствии доказательств."),
            Mistake(slug="Hyperbole", description="Гипербола — преувеличение для усиления аргумента."),
        ]


class ExtendedMistakeCatalog(MistakeCatalog):
    def list(self) -> List[Mistake]:
        return [
            Mistake(slug="Ad Hominem", description="Атака на личность вместо аргумента."),
            Mistake(slug="Straw Man", description="Искажение аргумента оппонента."),
            Mistake(slug="Complex Question", description="Многовопросие, подразумевает спорные посылки."),
            Mistake(slug="False Accusation of Lack of Evidence", description="Ложное обвинение в отсутствии доказательств."),
            Mistake(slug="Hyperbole", description="Гипербола — преувеличение."),
            Mistake(slug="Change of Subject", description="Смена предмета обсуждения."),
            Mistake(slug="Insinuation", description="Намёки/косвенные обвинения."),
            Mistake(slug="False Suspicion", description="Необоснованные подозрения."),
            Mistake(slug="Categorical Disagreement", description="Категорическое несогласие без аргументов."),
            Mistake(slug="Authoritarian Style", description="Опора на авторитет/власть вместо фактов."),
            Mistake(slug="Lady's Argument", description="Эмоциональные аргументы вне сути."),
            Mistake(slug="Imposed Consequence", description="Навязанное следствие как единственный исход."),
            Mistake(slug="Fact Sifting", description="Выборочное использование фактов."),
            Mistake(slug="Suspicion Construction", description="Конструирование подозрений."),
            Mistake(slug="Ironic Repetition", description="Ироническое повторение аргументов оппонента."),
        ]
