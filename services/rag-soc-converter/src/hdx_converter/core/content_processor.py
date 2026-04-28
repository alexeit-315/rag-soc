# core/content_processor.py - ПОЛНЫЙ ФАЙЛ С ИЗМЕНЕНИЯМИ

from typing import Tuple, List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup, Tag, NavigableString
from pathlib import Path
import re
import logging
import html
import json
from datetime import datetime
from ..parsers.html_parser import HTMLParser
from ..parsers.link_processor import LinkProcessor
from ..utils.image_processor import ImageProcessor
from ..models.schemas import SectionStructure, SectionType

class ContentProcessor:
    def __init__(self, config, path_resolver, image_processor: ImageProcessor, resolve_link_callback=None, logger: logging.Logger = None, stats_collector=None):
        """Инициализация процессора контента

        Args:
            config: конфигурация
            path_resolver: разрешитель путей
            image_processor: процессор изображений
            resolve_link_callback: callback для разрешения ссылок
            logger: экземпляр логгера, созданный в cli.py, с необходимым уровнем логирования
            stats_collector: сборщик статистики
        """
        self.config = config
        self.html_parser = HTMLParser()
        self.link_processor = LinkProcessor(path_resolver)
        self.image_processor = image_processor
        self.resolve_link_callback = resolve_link_callback
        self.logger = logger
        self.stats_collector = stats_collector

    def extract_content_with_links(self, soup: BeautifulSoup, source_file: Path) -> Tuple[Dict[str, Any], List, List]:
        """Извлечение контента в структурированном формате

        Возвращает: (structured_data, internal_links_legacy, external_links_legacy)
        """
        self.logger.debug(f"=== НАЧАЛО НОВОЙ ОБРАБОТКИ {source_file.name} ===")

        # Очистка HTML, но сохраняем навигацию в footer
        soup = self.html_parser.clean_html_content(soup)
        content_element = self.html_parser.find_main_content(soup)

        # Извлекаем заголовок статьи
        title_h1 = content_element.find(['h1', '.topicTitle-h1'])
        article_title = title_h1.get_text().strip() if title_h1 else ""
        if title_h1:
            self.logger.debug(f"Заголовок статьи: '{article_title}'")
            title_h1.decompose()

        # Временное логирование структуры дерева
        self.logger.debug(f"Структура content_element после удаления заголовка:")
        for i, child in enumerate(content_element.children):
            if isinstance(child, Tag):
                self.logger.debug(f"  Дитё {i}: {child.name} class={child.get('class', [])} text='{child.get_text(strip=True)[:50]}...'")

        # Инициализация структурированных данных
        structured_data = {
            "metadata": {
                "source_file": source_file.name,
                "source_path": str(source_file),
                "extraction_date": datetime.now().isoformat(),
                "article_title": article_title,
                "content_type": "structured_article",
                "version": "1.2"
            },
            "content": [],
            "links": {
                "internal": [],
                "external": []
            }
        }

        # Рекурсивно извлекаем все секции
        all_sections = self._extract_sections_flat(content_element, source_file)

        # Подсчитываем количество созданных секций Content
        content_sections_created = sum(1 for s in all_sections if s.get('type') == 'section' and s.get('title') == 'Content')

        # Добавляем все секции в structured_data
        structured_data["content"] = all_sections

        # Логируем статистику
        if content_sections_created > 0:
            self.logger.info(f"Всего создано секций Content: {content_sections_created}")
            if self.stats_collector:
                self.stats_collector.increment_content_sections_created(content_sections_created)

        # Обработка навигации в footer - выносим в отдельное поле
        navigation_links = self._process_footer_navigation(soup, source_file)
        if navigation_links:
            structured_data["navigation"] = navigation_links
            self.logger.debug(f"Добавлена навигация: {len(navigation_links)} ссылок")

        # Собираем все ссылки из структурированного контента
        structured_data = self._collect_links_from_structured_data(structured_data)

        self.logger.debug(f"=== СТРУКТУРИРОВАННЫЕ ДАННЫЕ ДЛЯ {source_file.name} ===")
        self.logger.debug(f"Sections: {len(structured_data['content'])}, "
                     f"Internal links: {len(structured_data['links']['internal'])}, "
                     f"External links: {len(structured_data['links']['external'])}")

        # Для обратной совместимости создаем legacy форматы
        internal_links_legacy = []
        external_links_legacy = []

        for link in structured_data["links"]["internal"]:
            internal_links_legacy.append((
                link.get("text", ""),
                link.get("href", ""),
                ""  # target будет заполнен позже
            ))

        for link in structured_data["links"]["external"]:
            external_links_legacy.append({
                "text": link.get("text", ""),
                "url": link.get("href", "")
            })

        self.logger.debug(f"Created legacy links: internal={len(internal_links_legacy)}, external={len(external_links_legacy)}")

        return structured_data, internal_links_legacy, external_links_legacy

    def _process_section(self, section_div: Tag, source_file: Path) -> Optional[Dict]:
        """Обработка секции (div.section)"""
        self.logger.debug(f"_process_section: начало обработки секции")
        self.logger.debug(f"  Содержимое секции: '{section_div.get_text(strip=True)[:200]}...'")

        # Проверяем, есть ли внутри дочерние элементы
        children_count = len([c for c in section_div.children if isinstance(c, Tag)])
        self.logger.debug(f"  Дочерних элементов: {children_count}")

        # Ищем заголовки любого уровня h2-h6 с классом sectiontitle
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        self.logger.debug(f"  Найден заголовок: {header is not None}")

        if not header:
            self.logger.debug(f"Секция без заголовка, обрабатываем весь контент")
            # Обрабатываем всё содержимое секции
            section_content = self._collect_element_content(section_div, source_file, "")

            if not section_content:
                return None

            return {
                "type": "section",
                "title": "Content",  # Заголовок по умолчанию для секций без заголовка
                "content": section_content
            }

        section_title = header.get_text().strip()

        # Собираем содержимое секции
        section_content = []
        current_element = header.find_next_sibling()

        while current_element and not (current_element.name == 'div' and 'section' in current_element.get('class', [])):
            element_data = self._process_element(current_element, source_file, section_title)
            if element_data:
                if isinstance(element_data, list):
                    section_content.extend(element_data)
                else:
                    section_content.append(element_data)

            current_element = current_element.find_next_sibling()

        return {
            "type": "section",
            "title": section_title,
            "content": section_content
        }

    def _process_general_content(self, container: Tag, source_file: Path, section_title: str) -> Optional[Dict]:
        """Обработка контента без явных секций"""

        # === ИСПРАВЛЕНИЕ: Сначала ищем специальные секции ===
        # Классы специальных секций
        special_classes = ['clifunc', 'cliformat', 'cliparam', 'cliview', 'cliexample', 'clidesc', 'clidefaultlevel']

        for special_class in special_classes:
            special_divs = container.find_all('div', class_=special_class)
            if special_divs:
                # Если нашли специальные секции, обрабатываем их
                sections = []
                for div in special_divs:
                    section_data = self._process_special_section(div, source_file, special_class)
                    if section_data:
                        sections.append(section_data)
                if sections:
                    return {
                        "type": "section",
                        "title": section_title,
                        "content": sections
                    }
        # === КОНЕЦ ИСПРАВЛЕНИЯ ===

        content_elements = self._collect_element_content(container, source_file, section_title)

        if not content_elements:
            return None

        return {
            "type": "section",
            "title": section_title,
            "content": content_elements
        }

    # === НОВЫЙ МЕТОД: Обработка специальных секций ===
    def _process_special_section(self, section_div: Tag, source_file: Path, section_class: str) -> Optional[Dict]:
        """Обработка специальных секций (clifunc, cliformat, cliparam, cliview, cliexample)"""

        # Определяем заголовок секции на основе класса
        section_titles = {
            'clifunc': 'Function',
            'cliformat': 'Format',
            'cliparam': 'Parameters',
            'cliview': 'Views',
            'cliexample': 'Example'
        }

        section_title = section_titles.get(section_class, section_class.capitalize())

        # Ищем заголовок внутри секции
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        if header:
            # Используем найденный заголовок
            section_title = header.get_text().strip()
            # Удаляем заголовок, чтобы он не дублировался в контенте
            header.decompose()

        self.logger.debug(f"Обработка специальной секции: class='{section_class}', title='{section_title}'")

        # Обрабатываем содержимое секции
        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "section",
            "title": section_title,
            "content": section_content
        }
    # === КОНЕЦ НОВОГО МЕТОДА ===

    def _collect_element_content(self, element, source_file: Path, context: str) -> List[Dict]:
        """Рекурсивный сбор всего контента элемента"""
        content_elements = []

        for child in element.children:
            child_data = self._process_child_element(child, source_file, context)
            if child_data:
                if isinstance(child_data, list):
                    content_elements.extend(child_data)
                else:
                    content_elements.append(child_data)

        return content_elements

    def _process_child_element(self, child, source_file: Path, context: str) -> Optional[Union[Dict, List[Dict]]]:
        """Обработка дочернего элемента"""

        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                self.logger.debug(f"Обработка текстовой строки: '{text[:50]}...'")
                return {"type": "text", "content": text}
            return None

        if not isinstance(child, Tag):
            return None

        # Добавлено логирование для диагностики
        element_text_preview = child.get_text(strip=True)[:100] if child.get_text(strip=True) else "ПУСТОЙ"
        self.logger.debug(f"Обработка элемента: name='{child.name}', class='{child.get('class', [])}', text='{element_text_preview}...'")

        # Добавлена проверка для <pre class="screen"> на верхнем уровне
        if child.name == 'pre' and 'screen' in child.get('class', []):
            self.logger.debug(f"Найден <pre class='screen'> на верхнем уровне")
            return self._process_code_block(child, source_file, context)

        # === ИСПРАВЛЕНИЕ: Добавлена проверка для таблиц ===
        if child.name == 'table':
            self.logger.debug(f"Найдена таблица на верхнем уровне")
            return self._process_table(child, source_file, context)
        # === КОНЕЦ ИСПРАВЛЕНИЯ ===

        # === НОВОЕ: Обработка div.steps ===
        if child.name == 'div' and 'steps' in child.get('class', []):
            self.logger.debug(f"Найден div.steps - последовательность действий")
            return self._process_steps_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка div.prereq ===
        if child.name == 'div' and 'prereq' in child.get('class', []):
            self.logger.debug(f"Найден div.prereq - предусловия")
            return self._process_prerequisite_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка div.postreq ===
        if child.name == 'div' and 'postreq' in child.get('class', []):
            self.logger.debug(f"Найден div.postreq - постусловия")
            return self._process_postrequisite_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка admonition (note, caution, danger, warning) ===
        if child.name == 'div':
            classes = child.get('class', [])
            admonition_types = ['note', 'caution', 'danger', 'warning']
            for adv_type in admonition_types:
                if adv_type in classes:
                    self.logger.debug(f"Найден div.{adv_type} - предупреждение/примечание")
                    return self._process_admonition_section(child, source_file, context, adv_type)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка div.example ===
        if child.name == 'div' and 'example' in child.get('class', []):
            self.logger.debug(f"Найден div.example - пример")
            return self._process_example_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка div.logRef* ===
        if child.name == 'div':
            classes = child.get('class', [])
            if any(cls.startswith('logRef') for cls in classes):
                self.logger.debug(f"Найден div с logRef классом - сообщение лога")
                return self._process_log_message_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        # === НОВОЕ: Обработка div.fignone ===
        if child.name == 'div' and 'fignone' in child.get('class', []):
            self.logger.debug(f"Найден div.fignone - фигура с подписью")
            return self._process_figure_section(child, source_file, context)
        # === КОНЕЦ НОВОГО ===

        if child.name == 'p':
            try:
                result = self._process_paragraph(child, source_file, context)
                if result and result.get('type') == 'paragraph':
                    content_preview = result.get('content', '')
                    if isinstance(content_preview, str):
                        self.logger.debug(f"Обработан параграф: '{content_preview[:100]}...'")
                    elif isinstance(content_preview, list):
                        self.logger.debug(f"Обработан параграф: {len(content_preview)} элементов")
                return result
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке параграфа {context}: {e}")
                return None

        elif child.name == 'ul' and 'ullinks' in child.get('class', []):
            try:
                self.logger.debug(f"Найден ul class='ullinks': найдено ссылок внутри: {len(child.find_all('a', recursive=True))}")
                return self._process_ullinks_list(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке ullinks списка {context}: {e}")
                return None

        elif child.name in ['ul', 'ol']:
            try:
                list_type = "упорядоченный" if child.name == 'ol' else "неупорядоченный"
                items_count = len(child.find_all('li', recursive=False))
                self.logger.debug(f"Найден список ({list_type}): {items_count} элементов")
                return self._process_list(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке списка {context}: {e}")
                return None

        elif child.name == 'li':
            try:
                item_text = child.get_text(strip=True)[:100] if child.get_text(strip=True) else "ПУСТОЙ"
                self.logger.debug(f"Найден элемент списка: '{item_text}...'")
                return self._process_list_item(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке элемента списка {context}: {e}")
                return None

        elif child.name == 'a':
            try:
                href = child.get('href', 'НЕТ ССЫЛКИ')
                link_text = child.get_text(strip=True)[:30] if child.get_text(strip=True) else "БЕЗ ТЕКСТА"
                self.logger.debug(f"Найдена ссылка: href='{href}', text='{link_text}...'")
                return self._process_link(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке ссылки {context}: {e}")
                return None

        elif child.name == 'img':
            try:
                src = child.get('src', 'НЕТ SRC')
                alt = child.get('alt', child.get('title', 'БЕЗ ALT'))[:50]
                self.logger.debug(f"Найдено изображение: src='{src}', alt='{alt}...'")
                return self._process_image(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке изображения {context}: {e}")
                return None

        elif child.name == 'span' and child.get_text(strip=True):
            try:
                text = child.get_text(separator=' ', strip=False).strip()
                if not text:
                    return None

                # === НОВОЕ: Проверка на semantic_role ===
                classes = child.get('class', [])
                result = {"type": "text", "content": text}

                if 'cmdname' in classes:
                    result["semantic_role"] = "cmdname"
                elif 'varname' in classes:
                    result["semantic_role"] = "varname"
                elif 'uicontrol' in classes:
                    result["semantic_role"] = "uicontrol"
                elif 'parmname' in classes:
                    result["semantic_role"] = "parmname"
                elif 'keyword' in classes:
                    result["semantic_role"] = "keyword"
                # === КОНЕЦ НОВОГО ===

                self.logger.debug(f"Обработка span: результат='{text[:100]}...'")
                return result
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке span {context}: {e}")
                return None

        elif child.name in ['b', 'strong', 'i', 'em']:
            try:
                text = child.get_text(separator=' ', strip=False).strip()
                self.logger.debug(f"Обработка форматированного элемента {child.name}: текст='{text[:100]}...'")
                return {"type": "text", "content": text} if text else None
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке форматированного элемента {child.name} в {context}: {e}")
                return None

        elif child.name == 'div' and 'p' in child.get('class', []):
            try:
                self.logger.debug(f"Найден div class='p', обрабатываем содержимое")
                return self._collect_element_content(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке div.p в {context}: {e}")
                return None

        else:
            try:
                self.logger.debug(f"Элемент '{child.name}' передан в _collect_element_content")
                return self._collect_element_content(child, source_file, context)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке элемента {child.name} в {context}: {e}")
                return None

    def _process_element(self, element, source_file: Path, context: str) -> Optional[Union[Dict, List[Dict]]]:
        """Алиас для _process_child_element для обратной совместимости"""
        return self._process_child_element(element, source_file, context)

    def _process_paragraph(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка параграфа"""
        paragraph_content = []

        for child in element.children:
            try:
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        paragraph_content.append({"type": "text", "content": text})

                elif isinstance(child, Tag) and child.name == 'a':
                    link_data = self._extract_link_data(child, source_file, context)
                    if link_data:
                        if link_data["type"] in ["internal", "external"]:
                            paragraph_content.append({
                                "type": "link",
                                "text": link_data["text"],
                                "href": link_data["href"],
                                "link_type": link_data["type"]
                            })
                        else:
                            if link_data["text"]:
                                paragraph_content.append({"type": "text", "content": link_data["text"]})

                else:
                    # Проверяем, не является ли дочерний элемент <pre class="screen">
                    if child.name == 'pre' and 'screen' in child.get('class', []):
                        # Если это блок кода, обрабатываем его как code_block
                        code_block = self._process_code_block(child, source_file, context)
                        if code_block:
                            paragraph_content.append(code_block)
                    else:
                        # Иначе обрабатываем обычным образом
                        nested_content = self._collect_element_content(child, source_file, context)
                        if nested_content:
                            paragraph_content.extend(nested_content)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке дочернего элемента параграфа в {context}: {e}")
                continue

        # Упрощаем структуру, если только текст
        if len(paragraph_content) == 1 and paragraph_content[0]["type"] == "text":
            result = {"type": "paragraph", "content": paragraph_content[0]["content"]}
        else:
            result = {"type": "paragraph", "content": paragraph_content}

        # Добавлено логирование
        if isinstance(result.get('content'), str):
            content_preview = result['content'][:100] if len(result['content']) > 100 else result['content']
            self.logger.debug(f"Обработан параграф: '{content_preview}...' (тип: простой текст)")
        else:
            self.logger.debug(f"Обработан параграф: {len(paragraph_content)} элементов (тип: сложная структура)")

        return result

    def _process_list(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка списка"""
        list_type = "unordered" if element.name == 'ul' else "ordered"
        list_items = []

        for li in element.find_all('li', recursive=False):
            try:
                item_data = self._process_list_item(li, source_file, context)
                if item_data:
                    list_items.append(item_data)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке элемента списка в {context}: {e}")
                continue

        result = {
            "type": "list",
            "list_type": list_type,
            "items": list_items
        }

        self.logger.debug(f"Обработан список ({list_type}): {len(list_items)} элементов")

        return result

    def _process_list_item(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка пункта списка"""
        item_content = []

        for child in element.children:
            try:
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        item_content.append({"type": "text", "content": text})
                elif isinstance(child, Tag):
                    # Проверяем, не является ли элемент <pre class="screen">
                    if child.name == 'pre' and 'screen' in child.get('class', []):
                        code_block = self._process_code_block(child, source_file, context)
                        if code_block:
                            item_content.append(code_block)
                    elif child.name == 'p':
                        # Особый случай: если внутри <p> только <pre>, обрабатываем напрямую
                        pre_element = child.find('pre', class_='screen')
                        if pre_element and len(list(child.children)) == 1:
                            code_block = self._process_code_block(pre_element, source_file, context)
                            if code_block:
                                item_content.append(code_block)
                        else:
                            # Иначе обрабатываем как обычный параграф
                            p_content = self._process_paragraph(child, source_file, context)
                            if p_content:
                                item_content.append(p_content)
                    else:
                        nested = self._process_child_element(child, source_file, context)
                        if nested:
                            if isinstance(nested, list):
                                item_content.extend(nested)
                            else:
                                item_content.append(nested)
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке дочернего элемента списка в {context}: {e}")
                continue

        if len(item_content) == 1 and item_content[0]["type"] == "text":
            return {"type": "list_item", "text": item_content[0]["content"]}
        elif not item_content:
            return {"type": "list_item", "text": ""}
        else:
            return {"type": "list_item", "content": item_content}

    def _process_code_block(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка блока кода"""
        try:
            code_text = self._extract_cli_command_simple(element)
        except Exception as e:
            self.logger.debug(f"Ошибка при извлечении текста из code_block в {context}: {e}")
            code_text = ""

        links_in_code = []
        for link in element.find_all('a', recursive=True):
            try:
                link_data = self._extract_link_data(link, source_file, context)
                if link_data and link_data["type"] in ["internal", "external"]:
                    links_in_code.append({
                        "text": link_data["text"],
                        "href": link_data["href"],
                        "link_type": link_data["type"]
                    })
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке ссылки в code_block в {context}: {e}")
                continue

        code_data = {
            "type": "code_block",
            "content": code_text,
            "language": "cli"
        }

        if links_in_code:
            code_data["links"] = links_in_code

        self.logger.debug(f"=== ОБРАБОТКА БЛОКА КОДА ===")
        self.logger.debug(f"  Контекст: {context}")
        self.logger.debug(f"  Тип: code_block")
        self.logger.debug(f"  Язык: cli")
        self.logger.debug(f"  Содержимое: '{code_text[:200]}...'")
        self.logger.debug(f"  Ссылок в коде: {len(links_in_code)}")
        self.logger.debug(f"  Длина: {len(code_text)} символов")
        self.logger.debug(f"=== КОНЕЦ БЛОКА КОДА ===")

        return code_data

    def _process_link(self, element: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка ссылки"""
        try:
            link_data = self._extract_link_data(element, source_file, context)
            if not link_data:
                return None

            if link_data["type"] in ["internal", "external"]:
                return {
                    "type": "link",
                    "text": link_data["text"],
                    "href": link_data["href"],
                    "link_type": link_data["type"]
                }

            return {"type": "text", "content": link_data["text"]}
        except Exception as e:
            self.logger.debug(f"Ошибка при обработке ссылки в {context}: {e}")
            return None

    def _process_image(self, element: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка изображения"""
        try:
            src = element.get('src', '').strip()
            alt = element.get('alt', '').strip() or element.get('title', '').strip()

            # добавляем default alt текст если alt пустой
            if not alt:
                alt = "Image"

            if not src:
                return None

            # Копируем изображение
            image_path = self.image_processor.copy_image(src, source_file)

            if image_path:
                # Правильный путь к изображениям
                # images/ находится на том же уровне, что и /md_data, должно быть "../images/"
                # Преобразуем путь вида "images/note_3.0-en-us.png" в "../images/note_3.0-en-us.png"
                path_str = str(image_path)
                if path_str.startswith('images/'):
                    path_str = f"../{path_str}"

                return {
                    "type": "image",
                    "src": path_str,
                    "alt": alt
                }

            return None
        except Exception as e:
            self.logger.debug(f"Ошибка при обработке изображения в {context}: {e}")
            return None

    def _extract_link_data(self, element: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Извлечение данных из ссылки"""
        try:
            href = element.get('href', '').strip()
            text = element.get_text(strip=True)

            if not href or not text:
                return None

            # Определяем тип ссылки
            if href.startswith(('http://', 'https://')):
                link_type = "external"
            elif href.endswith('.html') or '.html#' in href:
                link_type = "internal"
            elif href.startswith('#'):
                link_type = "anchor"
            elif 'cmdqueryname=' in href:
                link_type = "special"
            else:
                link_type = "other"

            # Для внутренних ссылок используем resolve_link_callback
            if link_type == "internal" and self.resolve_link_callback:
                target_info = self.resolve_link_callback(href, source_file)
                if target_info and target_info.get('json_filename'):
                    # Заменяем оригинальный .html на полное .json имя с DC.Identifier
                    href = target_info['json_filename']

            return {
                "text": text,
                "href": href,
                "type": link_type
            }
        except Exception as e:
            self.logger.debug(f"Ошибка при извлечении данных из ссылки в {context}: {e}")
            return None

    # === НОВЫЕ МЕТОДЫ ДЛЯ ОБРАБОТКИ ТИПОВ ===

    def _process_steps_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции steps (последовательность действий)"""
        # Ищем заголовок
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Procedure"

        if header:
            header.decompose()

        # Обрабатываем содержимое
        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "steps",
            "title": section_title,
            "content": section_content
        }

    def _process_prerequisite_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции prerequisite (предусловия)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Prerequisites"

        if header:
            header.decompose()

        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "prerequisite",
            "title": section_title,
            "content": section_content
        }

    def _process_postrequisite_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции postrequisite (постусловия)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Postrequisites"

        if header:
            header.decompose()

        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "postrequisite",
            "title": section_title,
            "content": section_content
        }

    def _process_admonition_section(self, section_div: Tag, source_file: Path, context: str, adv_type: str) -> Optional[Dict]:
        """Обработка секции admonition (note, caution, danger, warning)"""
        # Ищем заголовок (может быть span с title)
        title_span = section_div.find('span', class_=f'{adv_type}title')
        if not title_span:
            # Может быть span.notetitle
            title_span = section_div.find('span', class_='notetitle')

        section_title = title_span.get_text().strip() if title_span else adv_type.capitalize()

        # Ищем body
        body_div = section_div.find('div', class_=f'{adv_type}body')
        if not body_div:
            body_div = section_div.find('div', class_='notebody')

        if not body_div and adv_type == 'notice':
            body_div = section_div.find('div', class_='noticebody')

        if not body_div:
            body_div = section_div

        if title_span:
            title_span.decompose()

        # Обрабатываем содержимое body
        section_content = self._collect_element_content(body_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "admonition",
            "title": section_title,
            "content": section_content
        }

    def _process_example_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции example (пример)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Example"

        if header:
            header.decompose()

        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "example",
            "title": section_title,
            "content": section_content
        }

    def _process_log_message_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции log_message (сообщение лога)"""
        # Собираем все части лога
        log_parts = []

        # logRefMessage - сообщение
        message_div = section_div.find('div', class_='logRefMessage')
        if message_div:
            message_body = message_div.find('div', class_='logRefMessagebody')
            if message_body:
                log_parts.append(self._collect_element_content(message_body, source_file, "Message"))

        # logRefDesc - описание
        desc_div = section_div.find('div', class_='logRefDesc')
        if desc_div:
            desc_body = desc_div.find('div', class_='logRefDescbody')
            if desc_body:
                log_parts.append(self._collect_element_content(desc_body, source_file, "Description"))

        # logRefLvl - уровень/параметры
        lvl_div = section_div.find('div', class_='logRefLvl')
        if lvl_div:
            lvl_body = lvl_div.find('div', class_='logRefParamsbody')
            if lvl_body:
                log_parts.append(self._collect_element_content(lvl_body, source_file, "Parameters"))

        # logRefCause - причина
        cause_div = section_div.find('div', class_='logRefCause')
        if cause_div:
            cause_body = cause_div.find('div', class_='logRefCausebody')
            if cause_body:
                log_parts.append(self._collect_element_content(cause_body, source_file, "Cause"))

        # Заголовок секции
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Log Message"

        if header:
            header.decompose()

        # Объединяем все части
        flat_content = []
        for part in log_parts:
            if isinstance(part, list):
                flat_content.extend(part)
            elif part:
                flat_content.append(part)

        if not flat_content:
            return None

        return {
            "type": "log_message",
            "title": section_title,
            "content": flat_content
        }

    def _process_figure_section(self, section_div: Tag, source_file: Path, context: str) -> Optional[Dict]:
        """Обработка секции figure (изображение с подписью)"""
        # Ищем изображение
        img = section_div.find('img')
        if not img:
            return None

        # Обрабатываем изображение
        img_data = self._process_image(img, source_file, context)
        if not img_data:
            return None

        # Ищем подпись
        figcap = section_div.find('span', class_='figcap')
        caption_text = figcap.get_text().strip() if figcap else ""

        # Убираем номер рисунка из подписи (например, "Figure 1 ")
        if caption_text.startswith('Figure'):
            import re
            caption_text = re.sub(r'^Figure\s+\d+\s+', '', caption_text)

        result = {
            "type": "figure",
            "image": img_data,
            "caption": caption_text
        }

        self.logger.debug(f"Обработана фигура: caption='{caption_text[:50]}...'")

        return result

    # === КОНЕЦ НОВЫХ МЕТОДОВ ===

    # === ИСПРАВЛЕНИЕ: Реализация метода _process_table с поддержкой списков ===
    def _process_table(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка таблицы - с поддержкой вложенных списков"""
        self.logger.debug(f"Обработка таблицы в контексте: {context}")

        try:
            # Извлекаем заголовок таблицы (caption)
            caption = element.find('caption')
            caption_text = caption.get_text().strip() if caption else ""

            # Извлекаем заголовки колонок
            header_row = []
            thead = element.find('thead')
            if thead:
                th_elements = thead.find_all('th')
                header_row = [th.get_text().strip() for th in th_elements]

            if not header_row:
                first_row = element.find('tr')
                if first_row:
                    th_elements = first_row.find_all('th')
                    if th_elements:
                        header_row = [th.get_text().strip() for th in th_elements]

            # Извлекаем строки данных - с поддержкой вложенных элементов
            rows_data = []
            tbody = element.find('tbody')
            rows_to_process = tbody.find_all('tr') if tbody else element.find_all('tr')

            for row in rows_to_process:
                if row.find('th') and not header_row:
                    continue

                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue

                row_cells = []
                for cell in cells:
                    # Проверяем вложенные элементы в ячейке
                    inner_list = cell.find(['ul', 'ol'])
                    inner_code = cell.find('pre', class_='screen')
                    inner_link = cell.find('a')

                    if inner_list:
                        list_data = self._process_list(inner_list, source_file, context)
                        row_cells.append(list_data)
                    elif inner_code:
                        code_data = self._process_code_block(inner_code, source_file, context)
                        row_cells.append(code_data)
                    elif inner_link:
                        link_data = self._process_link(inner_link, source_file, context)
                        row_cells.append(link_data)
                    else:
                        cell_text = cell.get_text().strip()
                        row_cells.append(cell_text)

                # Проверяем, не дублирует ли строка заголовок
                if header_row and row_cells == header_row:
                    continue
                rows_data.append(row_cells)

            table_data = {
                "type": "table",
                "caption": caption_text,
                "header": header_row,
                "rows": rows_data
            }

            self.logger.debug(f"Таблица обработана: caption='{caption_text}', "
                         f"заголовков={len(header_row)}, строк={len(rows_data)}")

            return table_data

        except Exception as e:
            self.logger.debug(f"Ошибка при обработке таблицы в {context}: {e}")
            return {
                "type": "table",
                "caption": "",
                "header": [],
                "rows": []
            }
    # === КОНЕЦ ИСПРАВЛЕНИЯ ===

    # Существующие методы для обратной совместимости

    def extract_section_structure(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлечение структуры разделов"""
        sections = []

        all_headers = []
        main_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        all_headers.extend(main_headers)

        section_headers = soup.find_all(['h4', 'h5', 'h6'], class_=lambda x: x and 'sectiontitle' in x)
        for header in section_headers:
            if header not in all_headers:
                all_headers.append(header)

        all_headers.sort(key=lambda x: x.sourceline if hasattr(x, 'sourceline') else 0)

        seen_titles = set()

        self.logger.debug(f"Найдено заголовков: {len(all_headers)}")

        for i, header in enumerate(all_headers):
            section_type = self.html_parser.determine_section_type(header)
            section_id = header.get('id', f"section_{i+1}")
            title = header.get_text().strip()

            if not title or title in seen_titles:
                if title in seen_titles:
                    self.logger.debug(f"Пропущен дубликат заголовка: '{title}'")
                continue

            has_content = self._has_content_between_headers(header, all_headers, i)

            if has_content:
                sections.append({
                    "section_id": section_id,
                    "title": title,
                    "type": section_type.value if hasattr(section_type, 'value') else str(section_type)
                })
                seen_titles.add(title)
                self.logger.debug(f"Добавлен заголовок {i+1}: '{title}' (тип: {section_type})")

        return sections

    def _has_content_between_headers(self, current_header, all_headers, current_index) -> bool:
        """Проверяет, есть ли контент между заголовками"""
        if current_index >= len(all_headers) - 1:
            next_element = current_header.find_next_sibling()
            while next_element:
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                if self._contains_non_header_content(next_element):
                    return True
                next_element = next_element.find_next_sibling()
            return False

        next_header = all_headers[current_index + 1]
        current = current_header.find_next_sibling()

        while current and current != next_header:
            if self._contains_non_header_content(current):
                return True
            current = current.find_next_sibling()

        return False

    def _contains_non_header_content(self, element) -> bool:
        """Проверяет, содержит ли элемент не-заголовочный контент"""
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return False

        if isinstance(element, str):
            return bool(element.strip())

        if hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            return bool(text)

        return False

    def process_images_in_content(self, soup: BeautifulSoup, html_file: Path, content: str) -> str:
        """Обработка изображений в контенте"""
        images = self.html_parser.extract_all_images(soup)

        self.logger.debug(f"Найдено изображений: {len(images)}")

        image_references = []

        for img in images:
            image_caption = img['alt'] or img['title'] or "Image"
            image_path = self.image_processor.copy_image(img['src'], html_file)

            if image_path:
                image_references.append(f"![{image_caption}]({image_path})")
                self.logger.debug(f"Скопировано изображение: {img['src']} -> {image_path}")
            else:
                image_references.append(f"![{image_caption}]({img['src']})")
                self.logger.debug(f"Изображение не скопировано: {img['src']}")

        if image_references:
            content += "\n\n" + "\n".join(image_references)

        return content

    def _extract_cli_command_simple(self, pre_element) -> str:
        """Извлечение CLI команды - СОХРАНЕНИЕ ПЕРЕНОСОВ СТРОК"""

        # Извлекаем текст с сохранением всех whitespace
        all_text = pre_element.get_text(strip=False)
        cleaned_text = html.unescape(all_text)

        # Сохраняем переносы строк, но убираем лишние пробелы/табы
        # Заменяем последовательности пробелов/табов на один пробел, но сохраняем \n
        lines = []
        for line in cleaned_text.split('\n'):
            # Убираем лишние пробелы в начале/конце строки
            line = line.strip()
            # Заменяем множественные пробелы/табы в строке на один пробел
            line = re.sub(r'[ \t]+', ' ', line)
            if line:
                lines.append(line)

        # Собираем обратно с переносами строк
        cleaned_text = '\n'.join(lines)

        self.logger.debug(f"Извлечение CLI команды (сохранены переносы строк):")
        self.logger.debug(f"  Исходный текст: '{all_text[:200]}...'")
        self.logger.debug(f"  Очищенный текст (первые 200 символов): '{cleaned_text[:200]}...'")
        self.logger.debug(f"  Длина: {len(all_text)} -> {len(cleaned_text)} символов")
        self.logger.debug(f"  Количество строк: {len(lines)}")

        return cleaned_text

    def _process_ullinks_list(self, element: Tag, source_file: Path, context: str) -> Dict:
        """Обработка списка ссылок (ul class='ullinks')

        Извлекает все <a> теги из списка, независимо от структуры <dl>/<dt>
        """
        list_items = []

        # Ищем все ссылки <a> внутри списка
        for link in element.find_all('a', recursive=True):
            try:
                link_data = self._extract_link_data(link, source_file, context)
                if link_data and link_data["type"] in ["internal", "external"]:
                    # Используем обновленный href из link_data
                    list_items.append({
                        "type": "list_item",
                        "content": [{
                            "type": "link",
                            "text": link_data["text"],
                            "href": link_data["href"],
                            "link_type": link_data["type"]
                        }]
                    })
            except Exception as e:
                self.logger.debug(f"Ошибка при обработке ссылки в ullinks в {context}: {e}")
                continue

        return {
            "type": "list",
            "list_type": "unordered",
            "items": list_items
        }

    def _process_result_section(self, section_div: Tag, source_file: Path) -> Optional[Dict]:
        """Обработка секции result (результат выполнения)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Result"

        if header:
            header.decompose()

        section_content = self._collect_element_content(section_div, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "result",
            "title": section_title,
            "content": section_content
        }

    def _process_impact_section(self, section_div: Tag, source_file: Path) -> Optional[Dict]:
        """Обработка секции impactonsystem (влияние на систему)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Impact on the System"

        if header:
            header.decompose()

        body = section_div.find('div', class_='impactonsystembody')
        if not body:
            body = section_div

        section_content = self._collect_element_content(body, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "impact",
            "title": section_title,
            "content": section_content
        }

    def _process_cause_section(self, section_div: Tag, source_file: Path) -> Optional[Dict]:
        """Обработка секции possiblecauses (возможные причины)"""
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        section_title = header.get_text().strip() if header else "Possible Causes"

        if header:
            header.decompose()

        body = section_div.find('div', class_='alarmpossbody')
        if not body:
            body = section_div

        section_content = self._collect_element_content(body, source_file, section_title)

        if not section_content:
            return None

        return {
            "type": "cause",
            "title": section_title,
            "content": section_content
        }

    def _collect_links_from_structured_data(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивно собирает ссылки из структурированных данных

        Обходит всю структуру content и собирает все ссылки в structured_data["links"]
        Возвращает обновленный structured_data
        """
        self.logger.debug(f"=== _collect_links_from_structured_data НАЧАЛО ===")

        def collect_from_element(element, depth=0):
            indent = "  " * depth
            if isinstance(element, dict):
                # Если это ссылка
                if element.get("type") == "link":
                    link_info = {
                        "text": element.get("text", ""),
                        "href": element.get("href", ""),
                        "link_type": element.get("link_type", "")
                    }

                    self.logger.debug(f"{indent}Найдена ссылка: text='{link_info['text'][:30]}...', href='{link_info['href']}', type='{link_info['link_type']}'")

                    # Добавляем в соответствующий список
                    if element.get("link_type") == "internal":
                        if link_info not in structured_data["links"]["internal"]:
                            structured_data["links"]["internal"].append(link_info)
                            self.logger.debug(f"{indent}  -> Добавлена во internal_links")
                        else:
                            self.logger.debug(f"{indent}  -> Уже есть во internal_links, пропускаем")
                    elif element.get("link_type") == "external":
                        if link_info not in structured_data["links"]["external"]:
                            structured_data["links"]["external"].append(link_info)
                            self.logger.debug(f"{indent}  -> Добавлена во external_links")
                        else:
                            self.logger.debug(f"{indent}  -> Уже есть во external_links, пропускаем")
                    else:
                        self.logger.debug(f"{indent}  -> Неизвестный тип ссылки: {element.get('link_type')}")

                # Рекурсивно обрабатываем вложенные элементы
                for key, value in element.items():
                    if key != "type":  # Пропускаем type чтобы избежать бесконечной рекурсии
                        self.logger.debug(f"{indent}Рекурсивный обход ключа: {key}, тип значения: {type(value)}")
                        collect_from_element(value, depth + 1)

            elif isinstance(element, list):
                self.logger.debug(f"{indent}Найден список: {len(element)} элементов")
                for i, item in enumerate(element):
                    self.logger.debug(f"{indent}  Элемент {i+1}/{len(element)}")
                    collect_from_element(item, depth + 1)

        # Собираем ссылки из всего контента
        self.logger.debug(f"Начало сбора ссылок из structured_data['content']")
        content_items = structured_data.get("content", [])
        self.logger.debug(f"Количество элементов в content: {len(content_items)}")

        for i, content_item in enumerate(content_items):
            self.logger.debug(f"Обработка content_item {i+1}/{len(content_items)}")
            collect_from_element(content_item)

        self.logger.debug(f"=== _collect_links_from_structured_data КОНЕЦ ===")
        self.logger.debug(f"  Найдено internal_links: {len(structured_data['links']['internal'])}")
        self.logger.debug(f"  Найдено external_links: {len(structured_data['links']['external'])}")

        return structured_data

    def _process_footer_navigation(self, soup: BeautifulSoup, source_file: Path) -> Optional[List[Dict]]:
        """Обработка навигации в footer
        Возвращает список ссылок
        """
        navigation_links = []

        # Ищем footer навигацию
        footer_nav = soup.find('div', class_='footerNavBar')
        if not footer_nav:
            return None

        # 1. Parent Topic ссылка
        parentlink_div = footer_nav.find('div', class_='parentlink')
        if parentlink_div:
            parent_link = parentlink_div.find('a')
            if parent_link:
                href = parent_link.get('href', '').strip()
                if href and href.lower().endswith('.html'):
                    # Используем callback для разрешения ссылки
                    if self.resolve_link_callback:
                        target_info = self.resolve_link_callback(href, source_file)
                        if target_info:
                            article_title = target_info.get('title', 'Parent Topic')
                            json_filename = target_info.get('json_filename', '')
                            if json_filename:
                                navigation_links.append({
                                    "type": "link",
                                    "text": f"Parent: {article_title}",
                                    "href": json_filename,
                                    "link_type": "internal"
                                })
                            else:
                                # Fallback: используем текст ссылки
                                link_text = parent_link.get_text(strip=True)
                                navigation_links.append({
                                    "type": "link",
                                    "text": f"Parent: {link_text}",
                                    "href": href.replace('.html', '.json'),
                                    "link_type": "internal"
                                })
                    else:
                        # Без callback используем простую логику
                        link_text = parent_link.get_text(strip=True)
                        navigation_links.append({
                            "type": "link",
                            "text": f"Parent: {link_text}",
                            "href": href.replace('.html', '.json'),
                            "link_type": "internal"
                        })

        # 2. Previous и Next topic ссылки
        bottom_nav = footer_nav.find('div', class_='bottomNavBtn')
        if bottom_nav:
            links = bottom_nav.find_all('a', href=True)

            for i, link in enumerate(links):
                href = link.get('href', '').strip()
                if not href or not href.lower().endswith('.html'):
                    continue

                # Определяем тип навигации
                nav_type = ""
                if i == 0:
                    nav_type = "Previous"
                else:
                    nav_type = "Next"

                # Используем callback для разрешения ссылки
                if self.resolve_link_callback:
                    target_info = self.resolve_link_callback(href, source_file)
                    if target_info:
                        article_title = target_info.get('title', f'{nav_type} Topic')
                        json_filename = target_info.get('json_filename', '')

                        # Очищаем текст от HTML тегов и символов < >
                        clean_title = re.sub(r'<[^>]+>', '', article_title).strip()
                        clean_title = clean_title.replace('<', '').replace('>', '')

                        if json_filename:
                            navigation_links.append({
                                "type": "link",
                                "text": f"{nav_type}: {clean_title}",
                                "href": json_filename,
                                "link_type": "internal"
                            })
                        else:
                            # Fallback
                            link_text = link.get_text(strip=True)
                            clean_link_text = re.sub(r'<[^>]+>', '', link_text).strip()
                            clean_link_text = clean_link_text.replace('<', '').replace('>', '')
                            navigation_links.append({
                                "type": "link",
                                "text": f"{nav_type}: {clean_link_text}",
                                "href": href.replace('.html', '.json'),
                                "link_type": "internal"
                            })
                else:
                    # Без callback используем простую логику
                    link_text = link.get_text(strip=True)
                    clean_link_text = re.sub(r'<[^>]+>', '', link_text).strip()
                    clean_link_text = clean_link_text.replace('<', '').replace('>', '')
                    navigation_links.append({
                        "type": "link",
                        "text": f"{nav_type}: {clean_link_text}",
                        "href": href.replace('.html', '.json'),
                        "link_type": "internal"
                    })

        if navigation_links:
            # Возвращаем структурированные данные навигации
            return navigation_links

        return None

    def _process_task_section(self, section_div: Tag, source_file: Path) -> Optional[Dict]:
        """Обработка task-секции (div.context или div.steps-unordered)"""

        # Ищем заголовки любого уровня h2-h6 с классом sectiontitle
        header = section_div.find(['h2', 'h3', 'h4', 'h5', 'h6'], class_='sectiontitle')
        # ИЗМЕНЕНИЕ: Если нет заголовка, создаем секцию с пустым заголовком
        if not header:
            self.logger.debug(f"Секция без заголовка, обрабатываем весь контент")
            # Обрабатываем всё содержимое секции
            section_content = self._collect_element_content(section_div, source_file, "")

            if not section_content:
                return None

            return {
                "type": "section",
                "title": "",  # Пустой заголовок для секций без заголовка
                "content": section_content
            }

        section_title = header.get_text().strip()

        # Собираем содержимое секции
        section_content = []
        current_element = header.find_next_sibling()

        while current_element and not (current_element.name == 'div' and 'section' in current_element.get('class', [])):
            element_data = self._process_element(current_element, source_file, section_title)
            if element_data:
                if isinstance(element_data, list):
                    section_content.extend(element_data)
                else:
                    section_content.append(element_data)

            current_element = current_element.find_next_sibling()
        # ИЗМЕНЕНИЕ КОНЕЦ

        return {
            "type": "section",
            "title": section_title,
            "content": section_content
        }

    def _process_general_content_for_list(self, elements: List, source_file: Path, section_title: str) -> Optional[Dict]:
        """Обработка списка элементов как одной секции Content

        Args:
            elements: список элементов (Tag или NavigableString) для обработки
            source_file: путь к исходному файлу
            section_title: заголовок секции

        Returns:
            Dict: структурированная секция или None
        """
        if not elements:
            return None

        content_elements = []
        for elem in elements:
            if isinstance(elem, NavigableString):
                text = str(elem).strip()
                if text:
                    content_elements.append({"type": "text", "content": text})
            elif isinstance(elem, Tag):
                child_data = self._process_child_element(elem, source_file, section_title)
                if child_data:
                    if isinstance(child_data, list):
                        content_elements.extend(child_data)
                    else:
                        content_elements.append(child_data)

        if not content_elements:
            return None

        return {
            "type": "section",
            "title": section_title,
            "content": content_elements
        }

    def _process_general_content_for_list(self, elements: List, source_file: Path, section_title: str) -> Optional[Dict]:
        """Обработка списка элементов как одной секции Content

        Args:
            elements: список элементов (Tag или NavigableString) для обработки
            source_file: путь к исходному файлу
            section_title: заголовок секции

        Returns:
            Dict: структурированная секция или None
        """
        if not elements:
            return None

        content_elements = []
        for elem in elements:
            if isinstance(elem, NavigableString):
                text = str(elem).strip()
                if text:
                    content_elements.append({"type": "text", "content": text})
            elif isinstance(elem, Tag):
                child_data = self._process_child_element(elem, source_file, section_title)
                if child_data:
                    if isinstance(child_data, list):
                        content_elements.extend(child_data)
                    else:
                        content_elements.append(child_data)

        if not content_elements:
            return None

        return {
            "type": "section",
            "title": section_title,
            "content": content_elements
        }

    def _extract_sections_flat(self, element: Tag, source_file: Path, level: int = 0) -> List[Dict]:
        """Рекурсивно извлекает секции из элемента, сохраняя плоскую структуру

        Args:
            element: элемент для обработки
            source_file: путь к исходному файлу
            level: уровень вложенности (для отладки)

        Returns:
            List[Dict]: список секций (плоский)
        """
        result = []
        pending_content = []

        for child in element.children:
            if not isinstance(child, Tag):
                text = str(child).strip()
                if text:
                    pending_content.append(child)
                continue

            classes = child.get('class', [])

            # Проверяем, является ли ребенок секцией
            if self._is_section_element(child):
                # Сохраняем накопленный контент как секцию Content
                if pending_content:
                    content_section = self._process_general_content_for_list(pending_content, source_file, "Content")
                    if content_section:
                        result.append(content_section)
                    pending_content = []

                # Обрабатываем секцию
                section_data = self._process_section_by_class(child, source_file, classes)
                if section_data:
                    result.append(section_data)
            else:
                # Проверяем, содержит ли ребенок внутри себя секции
                if self._contains_sections(child):
                    # Сохраняем накопленный контент
                    if pending_content:
                        content_section = self._process_general_content_for_list(pending_content, source_file, "Content")
                        if content_section:
                            result.append(content_section)
                        pending_content = []

                    # Рекурсивно обрабатываем контейнер, результат добавляем на текущий уровень
                    nested_sections = self._extract_sections_flat(child, source_file, level + 1)
                    result.extend(nested_sections)
                else:
                    # Обычный элемент без секций - добавляем в накопленный контент
                    pending_content.append(child)

        # Сохраняем остатки
        if pending_content:
            content_section = self._process_general_content_for_list(pending_content, source_file, "Content")
            if content_section:
                result.append(content_section)

        return result

    def _is_section_element(self, tag: Tag) -> bool:
        """Проверяет, является ли элемент секцией"""
        classes = tag.get('class', [])
        section_classes = [
            'context', 'steps', 'steps-unordered', 'example', 'postreq', 'prereq',
            'result', 'impactonsystem', 'possiblecauses', 'section',
            'note', 'notice', 'caution', 'danger', 'warning'
        ]
        if any(cls.startswith('logRef') for cls in classes):
            return True
        return any(cls in section_classes for cls in classes)

    def _contains_sections(self, element: Tag) -> bool:
        """Проверяет, содержит ли элемент внутри себя секции"""
        for child in element.find_all(recursive=True):
            if isinstance(child, Tag) and self._is_section_element(child):
                return True
        return False

    def _process_section_by_class(self, tag: Tag, source_file: Path, classes: List[str]) -> Optional[Dict]:
        """Обрабатывает секцию в зависимости от ее класса"""
        if 'context' in classes:
            return self._process_task_section(tag, source_file)
        elif 'steps' in classes or 'steps-unordered' in classes:
            return self._process_steps_section(tag, source_file, "")
        elif 'example' in classes:
            return self._process_example_section(tag, source_file, "")
        elif 'postreq' in classes:
            return self._process_postrequisite_section(tag, source_file, "")
        elif 'prereq' in classes:
            return self._process_prerequisite_section(tag, source_file, "")
        elif 'result' in classes:
            return self._process_result_section(tag, source_file)
        elif 'impactonsystem' in classes:
            return self._process_impact_section(tag, source_file)
        elif 'possiblecauses' in classes:
            return self._process_cause_section(tag, source_file)
        elif 'note' in classes or 'notice' in classes or 'caution' in classes or 'danger' in classes or 'warning' in classes:
            adv_type = next((a for a in ['note', 'notice', 'caution', 'danger', 'warning'] if a in classes), 'note')
            return self._process_admonition_section(tag, source_file, "", adv_type)
        elif any(cls.startswith('logRef') for cls in classes):
            return self._process_log_message_section(tag, source_file, "")
        elif 'section' in classes:
            return self._process_section(tag, source_file)
        return None