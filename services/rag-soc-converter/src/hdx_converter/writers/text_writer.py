# writers/text_writer.py - ПОЛНЫЙ ФАЙЛ С ИЗМЕНЕНИЯМИ

from pathlib import Path
import logging
from typing import Optional, Dict, Any
from ..writers.file_writer import FileWriter

class TextWriter:
    def __init__(self, config, logger: logging.Logger = None):
        self.config = config
        self.file_writer = FileWriter(config, logger=logger)
        self.logger = logger

    def format_text_content(self, title: str, content: str, navigation: str = "") -> str:
        """Форматирование текстового контента"""
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('# ') and title in line:
                continue
            cleaned_lines.append(line)

        cleaned_content = '\n'.join(cleaned_lines)
        return f"Title: {title}\n\n{cleaned_content}{navigation}"

    def save_text_file(self, content: str, base_filename: str,
                      output_dir: Path, title: str = "") -> Optional[Path]:
        """Сохранение текстового файла"""
        # Убираем .md если есть в конце
        if base_filename.lower().endswith('.md'):
            base_filename = base_filename[:-3]

        # Убираем .txt если уже есть (на всякий случай)
        if base_filename.lower().endswith('.txt'):
            base_filename = base_filename[:-4]

        # Добавляем .txt
        filename = f"{base_filename}.txt"

        return self.file_writer.save_file(content, filename, "", output_dir, title)

    def format_structured_content(self, structured_data: Dict[str, Any], navigation: str) -> str:
        """Форматирование структурированных данных в текст - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        logger = self.logger
        if logger:
            logger.debug("=== ФОРМАТИРОВАНИЕ STRUCTURED_DATA В ТЕКСТ ===")

        text_parts = []

        # Добавляем заголовок статьи
        article_title = structured_data.get("metadata", {}).get("article_title", "")
        if article_title:
            text_parts.append(f"# {article_title}\n")
            if logger:
                logger.debug(f"Добавлен заголовок: {article_title}")

        # Рекурсивная обработка контента
        def process_element(element, indent=0):
            if isinstance(element, dict):
                element_type = element.get("type")

                if element_type == "section":
                    title = element.get("title", "")
                    content = element.get("content", [])
                    if title:
                        text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                        text_parts.append(f"{'  ' * indent}{title.upper()}")
                        text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")
                    for item in content:
                        process_element(item, indent + 1)

                # === НОВОЕ: Обработка новых типов ===
                elif element_type == "steps":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}{title.upper()} - STEPS")
                    text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "example":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[EXAMPLE] {title.upper()}")
                    text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "prerequisite":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[PREREQUISITE] {title.upper()}")
                    text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "postrequisite":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[POSTREQUISITE] {title.upper()}")
                    text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "result":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'=' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[RESULT] {title.upper()}")
                    text_parts.append(f"{'=' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "impact":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'!' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[IMPACT] {title.upper()}")
                    text_parts.append(f"{'!' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "cause":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'?' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[CAUSE] {title.upper()}")
                    text_parts.append(f"{'?' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "admonition":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'!' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[WARNING] {title.upper()}")
                    text_parts.append(f"{'!' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "log_message":
                    title = element.get("title", "")
                    content = element.get("content", [])

                    text_parts.append(f"\n{'~' * (50 if indent == 0 else 40)}")
                    text_parts.append(f"{'  ' * indent}[LOG] {title.upper()}")
                    text_parts.append(f"{'~' * (50 if indent == 0 else 40)}\n")

                    for item in content:
                        process_element(item, indent + 1)

                elif element_type == "figure":
                    image_data = element.get("image", {})
                    caption = element.get("caption", "")

                    src = image_data.get("src", "")
                    text_parts.append(f"\n[IMAGE: {src}]")
                    if caption:
                        text_parts.append(f"Caption: {caption}")
                    text_parts.append("\n")
                # === КОНЕЦ НОВОГО ===

                elif element_type == "navigation":
                    # === ИСПРАВЛЕНИЕ: Обработка навигации из structured_data ===
                    links = element.get("links", [])
                    if links:
                        text_parts.append("\n" + "="*50 + "\n")
                        text_parts.append("NAVIGATION\n")
                        text_parts.append("="*50 + "\n")
                        for link in links:
                            text = link.get("text", "")
                            href = link.get("href", "")
                            text_parts.append(f"- {text} -> {href}\n")
                    # === КОНЕЦ ИСПРАВЛЕНИЯ ===

                elif element_type == "paragraph":
                    content_data = element.get("content", "")
                    if isinstance(content_data, str):
                        text_parts.append(f"{'  ' * indent}{content_data}\n")
                    elif isinstance(content_data, list):
                        for item in content_data:
                            process_element(item, indent)
                        text_parts.append("\n")

                elif element_type == "list":
                    items = element.get("items", [])
                    for i, item in enumerate(items):
                        process_element(item, indent)

                elif element_type == "list_item":
                    content = element.get("content", [])
                    text = element.get("text", "")
                    if text:
                        text_parts.append(f"{'  ' * indent}* {text}\n")
                    elif content:
                        text_parts.append(f"{'  ' * indent}* ")
                        for item in content:
                            process_element(item, indent)
                        text_parts.append("\n")

                elif element_type == "link":
                    text = element.get("text", "")
                    href = element.get("href", "")
                    text_parts.append(f"[{text}]")

                elif element_type == "code_block":
                    content = element.get("content", "")
                    text_parts.append(f"\n{'  ' * indent}```\n")
                    text_parts.append(f"{content}\n")
                    text_parts.append(f"{'  ' * indent}```\n\n")

                elif element_type == "image":
                    src = element.get("src", "")
                    alt = element.get("alt", "")
                    text_parts.append(f"\n[IMAGE: {src}] ({alt})\n\n")

                elif element_type == "table":
                    caption = element.get("caption", "")
                    header = element.get("header", [])
                    rows = element.get("rows", [])

                    if caption:
                        text_parts.append(f"\n{caption}\n")
                        text_parts.append("-" * len(caption) + "\n")

                    # Определяем ширину колонок
                    col_widths = []
                    if header:
                        col_widths = [len(h) for h in header]
                        for row in rows:
                            for i, cell in enumerate(row):
                                if isinstance(cell, dict):
                                    # Для вложенных элементов (списков) считаем длину текста
                                    cell_len = len(str(cell))
                                else:
                                    cell_len = len(str(cell))
                                if i < len(col_widths):
                                    col_widths[i] = max(col_widths[i], cell_len)
                                else:
                                    col_widths.append(cell_len)

                    # Формируем разделитель
                    if col_widths:
                        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

                        # Выводим заголовок
                        if header:
                            text_parts.append(separator + "\n")
                            header_line = "|"
                            for i, h in enumerate(header):
                                header_line += f" {h:<{col_widths[i]}} |"
                            text_parts.append(header_line + "\n")
                            text_parts.append(separator + "\n")

                        # Выводим строки данных
                        for row in rows:
                            row_line = "|"
                            for i, cell in enumerate(row):
                                if isinstance(cell, dict) and cell.get("type") == "list":
                                    # Обрабатываем вложенный список
                                    list_items = []
                                    for item in cell.get("items", []):
                                        if item.get("type") == "list_item":
                                            list_items.append(item.get("text", ""))
                                    cell_str = ", ".join(list_items)
                                else:
                                    cell_str = str(cell)
                                if i < len(col_widths):
                                    row_line += f" {cell_str:<{col_widths[i]}} |"
                                else:
                                    row_line += f" {cell_str} |"
                            text_parts.append(row_line + "\n")

                        if rows and not header:
                            text_parts.append(separator + "\n")

                        text_parts.append("\n")

                elif element_type == "text":
                    content = element.get("content", "")
                    semantic_role = element.get("semantic_role", "")

                    # === НОВОЕ: Добавляем маркеры для semantic_role ===
                    if semantic_role == "cmdname":
                        text_parts.append(f"[CMD:{content}]")
                    elif semantic_role == "varname":
                        text_parts.append(f"<{content}>")
                    elif semantic_role == "uicontrol":
                        text_parts.append(f"{{{content}}}")
                    elif semantic_role == "parmname":
                        text_parts.append(f"({content})")
                    elif semantic_role == "keyword":
                        text_parts.append(f"*{content}*")
                    else:
                        text_parts.append(content)
                    # === КОНЕЦ НОВОГО ===

            elif isinstance(element, list):
                for item in element:
                    process_element(item, indent)

        # Обрабатываем весь контент
        for content_item in structured_data.get("content", []):
            process_element(content_item)

        # === ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 8: Убрано добавление навигации из параметра navigation ===
        # Навигация уже обработана из structured_data
        # === КОНЕЦ ИСПРАВЛЕНИЯ ===

        if logger:
            logger.debug(f"=== ЗАВЕРШЕНО ФОРМАТИРОВАНИЕ STRUCTURED_DATA ===")
            logger.debug(f"Размер текстового контента: {len(''.join(text_parts))} символов")

        return ''.join(text_parts)