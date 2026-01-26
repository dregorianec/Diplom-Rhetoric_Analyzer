#!/usr/bin/env python3
"""
Rhetorical Fallacy Analyzer - CLI Entry Point

Пайплайн:
1. Поиск видео политика на YouTube
2. Скачивание видео
3. Транскрибация через Whisper
4. LLM анализ на риторические ошибки
5. Визуализация результатов
"""
import argparse
import logging
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from application.mistakes_catalog import ShortMistakeCatalog, ExtendedMistakeCatalog
from application.chunker import SlidingWindowChunker
from application.pipeline import FullPipeline, LegacyPipeline, JsonResultWriter, TranscriptSaver
from application.visualizer import MatplotlibVisualizer, load_results_from_file
from infrastructure.llm.litellm_client import LiteLLMChain
from infrastructure.storage.local import LocalVideoStorage
from infrastructure.youtube.search import YtDlpSearcher, RapidAPIYouTubeSearcher
from infrastructure.youtube.downloader import YtDlpDownloader
from infrastructure.transcriber.whisper import WhisperTranscriber
from infrastructure.transcript.file_provider import FileTranscriptProvider

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def speaker_fn_generic(chunk: str) -> str:
    """
    Универсальная функция определения спикера.
    Для транскриптов без явных спикеров возвращает 'speaker'.
    """
    return "speaker"


def split_into_sentences(text: str) -> list:
    """Разбивает текст на предложения."""
    import re
    # Убираем таймкоды [0.0s - 25.4s]
    text = re.sub(r'\[\d+\.\d+s\s*-\s*\d+\.\d+s\]\s*', '', text)
    # Разбиваем по предложениям
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def build_chunker(max_tokens: int = 4000, max_chunks: int = 8, for_transcript: bool = False) -> SlidingWindowChunker:
    """Создаёт chunker для разбиения текста."""
    if for_transcript:
        # Для транскриптов: меньше окно, разбиение по предложениям
        return SlidingWindowChunker(
            max_tokens=max_tokens,
            max_chunks=max_chunks,
            window_start=1,  # Начинаем с первого чанка
            split_fn=split_into_sentences,
            speaker_fn=speaker_fn_generic,
        )
    else:
        # Для дебатов: стандартные настройки
        return SlidingWindowChunker(
            max_tokens=6000,
            max_chunks=12,
            window_start=6,
            split_fn=lambda text: text.split("\n\n"),
            speaker_fn=speaker_fn_generic,
        )


def run_full_pipeline(args):
    """Запускает полный пайплайн: поиск → скачивание → транскрипция → анализ."""
    settings = get_settings()
    
    logger.info("=== Starting Full Pipeline ===")
    logger.info("Politician: %s", args.politician)
    
    # Инициализация компонентов
    video_storage = LocalVideoStorage(settings.videos_dir)
    
    # YouTube Search & Download (через yt-dlp, без API ключей)
    searcher = YtDlpSearcher()
    downloader = YtDlpDownloader(storage=video_storage)
    
    # Whisper Transcriber
    transcriber = WhisperTranscriber(
        model_path=settings.whisper_model_path,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        language=settings.whisper_language,
    )
    
    # LLM Analyzer (LiteLLM)
    analyzer = LiteLLMChain(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        api_base=settings.llm_api_base,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_s,
        use_logprobs=settings.llm_use_logprobs,
    )
    
    # Каталог ошибок
    catalog = ExtendedMistakeCatalog() if args.extended else ShortMistakeCatalog()
    
    # Chunker (для транскриптов с YouTube)
    chunker = build_chunker(for_transcript=True)
    
    # Writers
    result_writer = JsonResultWriter(settings.results_dir)
    transcript_saver = TranscriptSaver(settings.transcripts_dir)
    
    # Pipeline
    pipeline = FullPipeline(
        searcher=searcher,
        downloader=downloader,
        transcriber=transcriber,
        catalog=catalog,
        chunker=chunker,
        analyzer=analyzer,
        result_writer=result_writer,
        transcript_saver=transcript_saver,
    )
    
    # Запуск
    result = pipeline.run(
        politician_name=args.politician,
        max_videos=args.max_videos,
        max_groups=settings.analysis_max_groups if settings.analysis_max_groups > 0 else None,
        sleep_between_llm_calls_s=settings.llm_sleep_between_calls_s,
    )
    
    logger.info("=== Pipeline Complete ===")
    logger.info("Videos processed: %d", len(result.get("videos", [])))
    logger.info("Total mistakes found: %d", result.get("total_mistakes", 0))
    
    if result.get("results_path"):
        logger.info("Results saved to: %s", result["results_path"])
        
        # Визуализация
        if not args.no_plot:
            visualizer = MatplotlibVisualizer(
                output_dir=settings.results_dir,
                show_plots=not args.save_plot_only
            )
            results = load_results_from_file(Path(result["results_path"]))
            visualizer.plot_summary(results, args.politician)
    
    return result


def run_legacy_pipeline(args):
    """Запускает анализ готового транскрипта (совместимость со старым CLI)."""
    settings = get_settings()
    
    logger.info("=== Starting Legacy Pipeline ===")
    logger.info("Transcript: %s", args.transcript_path)
    
    # LLM Analyzer (LiteLLM)
    analyzer = LiteLLMChain(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        api_base=settings.llm_api_base,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_s,
        use_logprobs=settings.llm_use_logprobs,
    )
    
    # Каталог ошибок
    catalog = ExtendedMistakeCatalog() if args.extended else ShortMistakeCatalog()
    
    # Chunker (для транскриптов)
    chunker = build_chunker(for_transcript=True)
    
    # Writers
    result_writer = JsonResultWriter(settings.results_dir)
    transcript_provider = FileTranscriptProvider()
    
    # Pipeline
    pipeline = LegacyPipeline(
        catalog=catalog,
        chunker=chunker,
        analyzer=analyzer,
        writer=result_writer,
        transcript_provider=transcript_provider,
    )
    
    output = pipeline.run(
        transcript_path=Path(args.transcript_path),
        max_groups=settings.analysis_max_groups if settings.analysis_max_groups > 0 else None,
        sleep_between_llm_calls_s=settings.llm_sleep_between_calls_s,
    )
    
    logger.info("=== Analysis Complete ===")
    logger.info("Results saved to: %s", output)
    
    # Визуализация
    if not args.no_plot:
        visualizer = MatplotlibVisualizer(
            output_dir=settings.results_dir,
            show_plots=not args.save_plot_only
        )
        results = load_results_from_file(output)
        visualizer.plot_mistakes_by_speaker(results)
    
    return output


def run_local_file(args):
    """Анализирует локальный аудио/видео файл."""
    settings = get_settings()
    
    media_path = Path(args.file)
    if not media_path.exists():
        logger.error("File not found: %s", media_path)
        sys.exit(1)
    
    logger.info("=== Analyzing Local File ===")
    logger.info("File: %s", media_path)
    
    # Whisper Transcriber
    transcriber = WhisperTranscriber(
        model_path=settings.whisper_model_path,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
        language=settings.whisper_language,
    )
    
    # Транскрибация
    logger.info("Transcribing...")
    transcript = transcriber.transcribe(media_path)
    
    # Сохраняем транскрипт
    transcript_saver = TranscriptSaver(settings.transcripts_dir)
    video_id = media_path.stem
    transcript_saver.save(transcript, video_id)
    logger.info("Transcript saved. Length: %d characters", len(transcript.text))
    
    # LLM Analyzer (LiteLLM)
    analyzer = LiteLLMChain(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        api_base=settings.llm_api_base,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_s,
        use_logprobs=settings.llm_use_logprobs,
    )
    
    # Каталог ошибок
    catalog = ExtendedMistakeCatalog() if args.extended else ShortMistakeCatalog()
    
    # Chunker (для транскриптов)
    chunker = build_chunker(for_transcript=True)
    
    # Анализ - используем plain text без таймкодов
    logger.info("Analyzing for rhetorical fallacies...")
    groups = chunker.split(transcript.text)
    logger.info("Created %d chunk groups", len(groups))
    
    mistakes = catalog.list()
    all_results = []

    # 1 вызов на группу
    for idx, group in enumerate(groups[: settings.analysis_max_groups if settings.analysis_max_groups > 0 else len(groups)]):
        if group.items[-1].speaker == "other":
            continue
        try:
            analysis = analyzer.analyze_group(idx, group, mistakes)
            all_results.extend(analysis)
        except Exception as e:
            logger.warning("Analysis failed: %s", e)
    
    # Сохраняем результаты
    result_writer = JsonResultWriter(settings.results_dir)
    output = result_writer.write(all_results, prefix=f"analysis-{video_id}")
    
    logger.info("=== Analysis Complete ===")
    logger.info("Found %d mistakes", len(all_results))
    logger.info("Results saved to: %s", output)
    
    # Визуализация
    if not args.no_plot and all_results:
        visualizer = MatplotlibVisualizer(
            output_dir=settings.results_dir,
            show_plots=not args.save_plot_only
        )
        visualizer.plot_summary(all_results, args.name or video_id)
    
    return output


def run_visualize(args):
    """Визуализирует существующие результаты."""
    settings = get_settings()
    
    results_path = Path(args.results_file)
    if not results_path.exists():
        logger.error("Results file not found: %s", results_path)
        sys.exit(1)
    
    logger.info("Loading results from: %s", results_path)
    results = load_results_from_file(results_path)
    
    visualizer = MatplotlibVisualizer(
        output_dir=settings.results_dir,
        show_plots=not args.save_only
    )
    
    politician = args.politician or "Unknown"
    visualizer.plot_summary(results, politician)
    
    logger.info("Visualization complete")


def main():
    parser = argparse.ArgumentParser(
        description="Rhetorical Fallacy Analyzer - анализ риторических ошибок в речи политиков",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Полный пайплайн: поиск, скачивание, транскрипция, анализ
  python -m src.app analyze --politician "Donald Trump"
  
  # Анализ готового транскрипта
  python -m src.app legacy --transcript-path data/transcripts/speech.txt
  
  # Визуализация существующих результатов  
  python -m src.app visualize --results-file data/results/analysis-2024-01-01.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    
    # === Команда analyze (полный пайплайн) ===
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Полный пайплайн: поиск видео → скачивание → транскрипция → анализ"
    )
    analyze_parser.add_argument(
        "--politician", "-p",
        type=str,
        required=True,
        help="Имя политика для поиска (например, 'Donald Trump')"
    )
    analyze_parser.add_argument(
        "--max-videos", "-n",
        type=int,
        default=1,
        help="Максимальное количество видео для обработки (default: 1)"
    )
    analyze_parser.add_argument(
        "--extended", "-e",
        action="store_true",
        help="Использовать расширенный каталог ошибок (15 типов вместо 5)"
    )
    analyze_parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Не показывать графики"
    )
    analyze_parser.add_argument(
        "--save-plot-only",
        action="store_true",
        help="Только сохранить графики, не показывать"
    )
    
    # === Команда legacy (анализ готового транскрипта) ===
    legacy_parser = subparsers.add_parser(
        "legacy",
        help="Анализ готового транскрипта (без скачивания/транскрипции)"
    )
    legacy_parser.add_argument(
        "--transcript-path", "-t",
        type=str,
        required=True,
        help="Путь к файлу транскрипта"
    )
    legacy_parser.add_argument(
        "--extended", "-e",
        action="store_true",
        help="Использовать расширенный каталог ошибок"
    )
    legacy_parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Не показывать графики"
    )
    legacy_parser.add_argument(
        "--save-plot-only",
        action="store_true",
        help="Только сохранить графики"
    )
    
    # === Команда local (анализ локального файла) ===
    local_parser = subparsers.add_parser(
        "local",
        help="Анализ локального аудио/видео файла (транскрипция + анализ)"
    )
    local_parser.add_argument(
        "--file", "-f",
        type=str,
        required=True,
        help="Путь к аудио/видео файлу (.mp3, .wav, .mp4, etc.)"
    )
    local_parser.add_argument(
        "--name", "-n",
        type=str,
        help="Имя спикера для графиков (опционально)"
    )
    local_parser.add_argument(
        "--extended", "-e",
        action="store_true",
        help="Использовать расширенный каталог ошибок"
    )
    local_parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Не показывать графики"
    )
    local_parser.add_argument(
        "--save-plot-only",
        action="store_true",
        help="Только сохранить графики"
    )
    
    # === Команда visualize ===
    viz_parser = subparsers.add_parser(
        "visualize",
        help="Визуализация существующих результатов анализа"
    )
    viz_parser.add_argument(
        "--results-file", "-r",
        type=str,
        required=True,
        help="Путь к JSON файлу с результатами"
    )
    viz_parser.add_argument(
        "--politician", "-p",
        type=str,
        help="Имя политика для заголовка графиков"
    )
    viz_parser.add_argument(
        "--save-only",
        action="store_true",
        help="Только сохранить графики"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "analyze":
            run_full_pipeline(args)
        elif args.command == "legacy":
            run_legacy_pipeline(args)
        elif args.command == "local":
            run_local_file(args)
        elif args.command == "visualize":
            run_visualize(args)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
