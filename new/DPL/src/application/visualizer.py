"""
Визуализация результатов анализа риторических ошибок.
"""
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

from src.domain.interfaces import Visualizer
from src.domain.models import AnalysisResult

logger = logging.getLogger(__name__)

# Настройка шрифтов для поддержки кириллицы
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']


class MatplotlibVisualizer(Visualizer):
    """
    Визуализатор результатов анализа через Matplotlib.
    """

    def __init__(self, output_dir: Optional[Path] = None, show_plots: bool = True):
        self.output_dir = output_dir
        self.show_plots = show_plots
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

    def plot_mistakes_by_speaker(
        self,
        results: List[AnalysisResult],
        output_path: Optional[Path] = None,
        title: str = "Риторические ошибки по спикерам"
    ) -> None:
        """
        Строит bar chart ошибок по спикерам.
        
        Args:
            results: Список результатов анализа
            output_path: Путь для сохранения графика
            title: Заголовок графика
        """
        if not results:
            logger.warning("No results to visualize")
            return

        # Группируем по ошибкам и спикерам
        mistakes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        speakers = set()
        
        for r in results:
            mistakes[r.mistake_slug][r.speaker_slug] += 1
            speakers.add(r.speaker_slug)

        speakers = sorted(speakers)
        mistake_types = list(mistakes.keys())

        if not mistake_types:
            logger.warning("No mistakes found in results")
            return

        # Данные для графика
        x = np.arange(len(mistake_types))
        width = 0.8 / len(speakers)
        
        # Цвета для спикеров
        colors = plt.cm.Set2(np.linspace(0, 1, len(speakers)))

        fig, ax = plt.subplots(figsize=(12, 6))
        
        for i, speaker in enumerate(speakers):
            counts = [mistakes[m][speaker] for m in mistake_types]
            offset = (i - len(speakers)/2 + 0.5) * width
            bars = ax.bar(x + offset, counts, width, label=speaker, color=colors[i], alpha=0.8)
            
            # Добавляем значения над столбцами
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{int(height)}',
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=8)

        ax.set_ylabel('Количество ошибок')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(mistake_types, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info("Plot saved to: %s", output_path)
        elif self.output_dir:
            path = self.output_dir / "mistakes_by_speaker.png"
            plt.savefig(path, dpi=150, bbox_inches='tight')
            logger.info("Plot saved to: %s", path)

        if self.show_plots:
            plt.show()
        else:
            plt.close()

    def plot_mistakes_distribution(
        self,
        results: List[AnalysisResult],
        output_path: Optional[Path] = None,
        title: str = "Распределение типов ошибок"
    ) -> None:
        """
        Строит pie chart распределения типов ошибок.
        """
        if not results:
            logger.warning("No results to visualize")
            return

        # Подсчитываем ошибки по типам
        mistake_counts: Dict[str, int] = defaultdict(int)
        for r in results:
            mistake_counts[r.mistake_slug] += 1

        if not mistake_counts:
            logger.warning("No mistakes found")
            return

        labels = list(mistake_counts.keys())
        sizes = list(mistake_counts.values())
        colors = plt.cm.Pastel1(np.linspace(0, 1, len(labels)))

        fig, ax = plt.subplots(figsize=(10, 8))
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            explode=[0.02] * len(labels),
        )
        
        ax.set_title(title)
        
        # Улучшаем читаемость
        for autotext in autotexts:
            autotext.set_fontsize(9)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            logger.info("Plot saved to: %s", output_path)
        elif self.output_dir:
            path = self.output_dir / "mistakes_distribution.png"
            plt.savefig(path, dpi=150, bbox_inches='tight')
            logger.info("Plot saved to: %s", path)

        if self.show_plots:
            plt.show()
        else:
            plt.close()

    def plot_timeline(
        self,
        results: List[AnalysisResult],
        output_path: Optional[Path] = None,
        title: str = "Timeline ошибок"
    ) -> None:
        """
        Строит timeline ошибок по позиции в тексте.
        """
        if not results:
            return

        fig, ax = plt.subplots(figsize=(14, 6))

        # Группируем по спикерам
        speakers = sorted(set(r.speaker_slug for r in results))
        colors = plt.cm.Set1(np.linspace(0, 1, len(speakers)))
        color_map = dict(zip(speakers, colors))

        for r in results:
            ax.scatter(
                r.chunk_start_char_id,
                r.mistake_slug,
                c=[color_map[r.speaker_slug]],
                s=100,
                alpha=0.7,
                edgecolors='black',
                linewidths=0.5,
            )

        # Легенда
        for speaker, color in color_map.items():
            ax.scatter([], [], c=[color], label=speaker, s=100)
        
        ax.set_xlabel('Позиция в тексте (символы)')
        ax.set_ylabel('Тип ошибки')
        ax.set_title(title)
        ax.legend(loc='upper right')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        elif self.output_dir:
            plt.savefig(self.output_dir / "timeline.png", dpi=150, bbox_inches='tight')

        if self.show_plots:
            plt.show()
        else:
            plt.close()

    def plot_summary(
        self,
        results: List[AnalysisResult],
        politician_name: str,
        output_path: Optional[Path] = None
    ) -> None:
        """
        Создаёт сводный график с несколькими панелями.
        """
        if not results:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Анализ риторики: {politician_name}', fontsize=14, fontweight='bold')

        # 1. Bar chart по спикерам
        ax1 = axes[0, 0]
        self._plot_bar_on_axis(ax1, results, "Ошибки по спикерам")

        # 2. Pie chart
        ax2 = axes[0, 1]
        self._plot_pie_on_axis(ax2, results, "Распределение ошибок")

        # 3. Гистограмма по группам
        ax3 = axes[1, 0]
        self._plot_histogram_on_axis(ax3, results, "Ошибки по позиции")

        # 4. Текстовая статистика
        ax4 = axes[1, 1]
        self._plot_stats_on_axis(ax4, results, politician_name)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
        elif self.output_dir:
            plt.savefig(self.output_dir / f"summary_{politician_name.replace(' ', '_')}.png", dpi=150, bbox_inches='tight')

        if self.show_plots:
            plt.show()
        else:
            plt.close()

    def _plot_bar_on_axis(self, ax, results, title):
        """Вспомогательный метод для bar chart."""
        mistakes = defaultdict(lambda: defaultdict(int))
        speakers = set()
        
        for r in results:
            mistakes[r.mistake_slug][r.speaker_slug] += 1
            speakers.add(r.speaker_slug)

        speakers = sorted(speakers)
        mistake_types = list(mistakes.keys())

        if not mistake_types:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
            return

        x = np.arange(len(mistake_types))
        width = 0.8 / max(len(speakers), 1)
        colors = plt.cm.Set2(np.linspace(0, 1, max(len(speakers), 1)))

        for i, speaker in enumerate(speakers):
            counts = [mistakes[m][speaker] for m in mistake_types]
            offset = (i - len(speakers)/2 + 0.5) * width
            ax.bar(x + offset, counts, width, label=speaker, color=colors[i], alpha=0.8)

        ax.set_ylabel('Количество')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(mistake_types, rotation=45, ha='right', fontsize=8)
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

    def _plot_pie_on_axis(self, ax, results, title):
        """Вспомогательный метод для pie chart."""
        counts = defaultdict(int)
        for r in results:
            counts[r.mistake_slug] += 1

        if not counts:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
            return

        ax.pie(
            counts.values(),
            labels=counts.keys(),
            autopct='%1.0f%%',
            colors=plt.cm.Pastel1(np.linspace(0, 1, len(counts))),
            textprops={'fontsize': 8}
        )
        ax.set_title(title)

    def _plot_histogram_on_axis(self, ax, results, title):
        """Гистограмма позиций ошибок."""
        positions = [r.chunk_start_char_id for r in results]
        
        if not positions:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
            return

        ax.hist(positions, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel('Позиция в тексте')
        ax.set_ylabel('Количество ошибок')
        ax.set_title(title)
        ax.grid(axis='y', alpha=0.3)

    def _plot_stats_on_axis(self, ax, results, politician_name):
        """Текстовая статистика."""
        ax.axis('off')
        
        total = len(results)
        speakers = defaultdict(int)
        mistakes = defaultdict(int)
        
        for r in results:
            speakers[r.speaker_slug] += 1
            mistakes[r.mistake_slug] += 1

        # Самая частая ошибка
        top_mistake = max(mistakes.items(), key=lambda x: x[1]) if mistakes else ("N/A", 0)
        
        stats_text = f"""
        СТАТИСТИКА АНАЛИЗА
        ─────────────────────────
        Политик: {politician_name}
        Всего ошибок: {total}
        
        По спикерам:
        {chr(10).join(f"  • {s}: {c}" for s, c in sorted(speakers.items()))}
        
        Самая частая ошибка:
          {top_mistake[0]} ({top_mistake[1]} раз)
        
        Уникальных типов ошибок: {len(mistakes)}
        """
        
        ax.text(0.1, 0.9, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


def load_results_from_file(filepath: Path) -> List[AnalysisResult]:
    """Загружает результаты анализа из JSON файла."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for item in data:
        results.append(AnalysisResult(
            group_idx=item.get("group_idx", 0),
            speaker_slug=item.get("speaker_slug", "unknown"),
            mistake_slug=item.get("mistake_slug", "unknown"),
            group_start_char_id=item.get("group_start_char_id", 0),
            group_end_char_id=item.get("group_end_char_id", 0),
            chunk_start_char_id=item.get("chunk_start_char_id", 0),
            chunk_end_char_id=item.get("chunk_end_char_id", 0),
            reason=item.get("reason", ""),
            how_starts=item.get("how_starts", ""),
            how_ends=item.get("how_ends", ""),
        ))
    
    return results
