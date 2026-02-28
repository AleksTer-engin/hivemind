#!/usr/bin/env python3
"""
AI Assistant with Hands and Laboratory
- Полноценный ИИ-ассистент с доступом к файловой системе
- Поддержка команд и естественного языка
- Интеграция с локальной LLM (qwen3:8b)
- Лаборатория для сборки, диагностики и интеграции
"""

import os
import sys
import json
import time
import subprocess
import requests
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class AIAssistant:
    def __init__(self, project_dir, ollama_url="http://localhost:11434"):
        self.project_dir = Path(project_dir)
        self.ollama_url = ollama_url
        self.context = []
        self.project_dir.mkdir(exist_ok=True)
        
        # Инициализация памяти/RAG
        self.memory_file = self.work_dir / "memory.json"
        self.load_memory()
        
        # Загрузка онтологии
        self.ontology = {}
        self.load_ontology()
        
        print(f"ИИ-ассистент с руками и лабораторией запущен")
        print(f"Проект: {self.project_dir}")
        print(f"Онтология: {list(self.ontology.keys()) if self.ontology else 'не загружена'}")
        print(f"Команды: /help - справка, /lab - лаборатория")
    
    @property
    def work_dir(self):
        return self.project_dir
    
    # ==================== ОНТОЛОГИЯ ====================
    
    def load_ontology(self):
        """Загрузить YAML-файлы онтологии из astro/ontology"""
        import yaml
        
        # Ищем astro/ontology в home или в project_dir
        possible_paths = [
            Path.home() / "astro" / "ontology",
            self.project_dir / "astro" / "ontology",
            self.project_dir.parent / "astro" / "ontology"
        ]
        
        for ontology_dir in possible_paths:
            if ontology_dir.exists():
                print(f"📚 Загрузка онтологии из {ontology_dir}")
                for yaml_file in ontology_dir.glob("*.yaml"):
                    try:
                        with open(yaml_file, 'r', encoding='utf-8') as f:
                            name = yaml_file.stem
                            self.ontology[name] = yaml.safe_load(f)
                            print(f"  - загружен {name}.yaml")
                    except Exception as e:
                        print(f"  ⚠️ Ошибка загрузки {yaml_file.name}: {e}")
                
                # Загрузить маппинги
                mappings_dir = ontology_dir / "mappings"
                if mappings_dir.exists():
                    for yaml_file in mappings_dir.glob("*.yaml"):
                        try:
                            with open(yaml_file, 'r', encoding='utf-8') as f:
                                name = f"mapping_{yaml_file.stem}"
                                self.ontology[name] = yaml.safe_load(f)
                                print(f"  - загружен mappings/{yaml_file.name}")
                        except Exception as e:
                            print(f"  ⚠️ Ошибка загрузки mappings/{yaml_file.name}: {e}")
                break
        
        if not self.ontology:
            print("⚠️ Онтология не найдена. Работа без неё.")
    
    # ==================== ПАМЯТЬ/RAG ====================
    
    def load_memory(self):
        """Загрузить память из файла"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except:
                self.memory = {
                    "queries": [],
                    "files": {},
                    "classifications": [],
                    "contexts": []
                }
        else:
            self.memory = {
                "queries": [],
                "files": {},
                "classifications": [],
                "contexts": []
            }
    
    def save_memory(self):
        """Сохранить память в файл"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def remember_query(self, query, response, analysis=None):
        """Запомнить запрос и ответ"""
        self.memory["queries"].append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "analysis": analysis
        })
        # Оставляем последние 100 запросов
        self.memory["queries"] = self.memory["queries"][-100:]
        self.save_memory()
    
    def remember_file(self, filepath, analysis):
        """Запомнить анализ файла"""
        self.memory["files"][str(filepath)] = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        }
        self.save_memory()
    
    def search_memory(self, query):
        """Поиск по памяти (простой)"""
        results = []
        keywords = query.lower().split()
        
        # Ищем в запросах
        for q in self.memory["queries"]:
            score = sum(k in q["query"].lower() for k in keywords)
            if score > 0:
                results.append({
                    "type": "query",
                    "score": score,
                    "timestamp": q["timestamp"],
                    "content": q["query"],
                    "response": q.get("response", "")
                })
        
        # Ищем в файлах
        for fname, fdata in self.memory["files"].items():
            if fdata.get("analysis"):
                text = str(fdata["analysis"]).lower()
                score = sum(k in text for k in keywords)
                if score > 0:
                    results.append({
                        "type": "file",
                        "score": score,
                        "file": fname,
                        "analysis": fdata["analysis"]
                    })
        
        results.sort(key=lambda x: -x["score"])
        return results[:5]
    
    # ==================== ЗАПРОСЫ К LLM ====================
    
    def ask_ollama(self, prompt, system=None, temperature=0.7, max_tokens=1000):
        """Отправить запрос в локальную модель"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "qwen3:8b",  # или другая твоя модель
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                return f"Ошибка модели: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return "Ошибка: Не удалось подключиться к ollama. Запустите 'ollama serve'"
        except Exception as e:
            return f"Ошибка: {e}"
    
    # ==================== РАБОТА С ФАЙЛАМИ ====================
    
    def read_file(self, filepath):
        """Прочитать файл из проекта"""
        full_path = self.work_dir / filepath
        if full_path.exists():
            if full_path.is_file():
                return full_path.read_text(encoding='utf-8')
            else:
                return f"{filepath} — это папка"
        return f"Файл {filepath} не найден"
    
    def write_file(self, filepath, content):
        """Записать файл в проект"""
        full_path = self.work_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        return f"Файл {filepath} записан ({len(content)} символов)"
    
    def list_files(self, path="."):
        """Показать файлы в директории"""
        full_path = self.work_dir / path
        if not full_path.exists():
            return f"Путь {path} не найден"
        
        if full_path.is_file():
            return f"{path} — это файл"
        
        files = []
        for f in sorted(full_path.iterdir()):
            size = f.stat().st_size if f.is_file() else 0
            modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            type_char = "📄" if f.is_file() else "📁"
            files.append(f"{type_char} {f.name}  ({size} bytes)  [{modified}]")
        
        return "\n".join(files)
    
    def handle_file_request(self, path):
        """Обработать запрос на просмотр файлов/папок"""
        target = Path(path).expanduser()
        if not target.exists():
            return f"Путь {path} не существует"
        
        if target.is_dir():
            result = f"\n📁 {path}:\n"
            files = list(target.glob("*"))
            for i, f in enumerate(sorted(files)[:20]):
                size = f.stat().st_size if f.is_file() else 0
                modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                type_char = "📄" if f.is_file() else "📁"
                result += f"  {type_char} {f.name}  ({size} bytes)  [{modified}]\n"
            if len(files) > 20:
                result += f"  ... и ещё {len(files)-20}\n"
            return result
        else:
            content = target.read_text(encoding='utf-8')[:2000]
            result = f"\n📄 {path}:\n"
            result += "-" * 50 + "\n"
            result += content + "\n"
            if target.stat().st_size > 2000:
                result += "-" * 50 + "\n"
                result += f"⚠️ Показаны первые 2000 из {target.stat().st_size} символов\n"
            return result
    
    # ==================== АНАЛИЗ ФАЙЛОВ ====================
    
    def analyze_content(self, filepath):
        """Проанализировать содержимое файла через LLM"""
        try:
            content = self.read_file(filepath)
            if len(content) > 3000:
                content = content[:3000] + "... (обрезано)"
            
            prompt = f"""Проанализируй этот файл и ответь строго в формате JSON:
{{
  "type": "actors|spheres|goals|values|mapping|code|config|docs|other",
  "subtype": "конкретный тип файла",
  "key_elements": ["список ключевых сущностей"],
  "matches_ontology": ["какие элементы из онтологии найдены"],
  "purpose": "краткое описание назначения (1 предложение)",
  "actions": ["что можно с ним сделать"]
}}

Файл: {filepath}
Содержимое:
{content}
"""
            response = self.ask_ollama(prompt, temperature=0.1)
            
            # Извлекаем JSON из ответа
            import json
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            try:
                data = json.loads(response)
                return data
            except:
                return {"error": "Не удалось распарсить JSON", "raw": response[:500]}
        except Exception as e:
            return {"error": str(e)}
    
    # ==================== ИНТЕГРАЦИЯ С HIVEMIND ====================
    
    def get_services_list(self):
        """Получить список сервисов из hivemind"""
        services = []
        hivemind_paths = [
            Path.home() / "hivemind" / "services",
            self.project_dir / "hivemind" / "services",
            self.project_dir.parent / "hivemind" / "services"
        ]
        
        for services_dir in hivemind_paths:
            if services_dir.exists():
                for service_dir in services_dir.iterdir():
                    if service_dir.is_dir():
                        services.append(service_dir.name)
                break
        
        return services if services else ["сервисы не найдены"]
    
    def check_hivemind_status(self):
        """Проверить статус HiveMind"""
        status = {
            "services": {},
            "nats": False,
            "databases": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверка docker-контейнеров
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            containers = result.stdout.strip().split('\n')
            
            # Ищем сервисы hivemind
            hivemind_containers = [c for c in containers if 'hivemind' in c or 
                                   any(x in c for x in ['nats', 'postgres', 'neo4j', 'qdrant', 'redis'])]
            
            for container in hivemind_containers:
                if container:
                    status["services"][container] = "running"
        except:
            status["docker"] = "недоступен"
        
        # Проверка NATS (простейшая)
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 4222))
            status["nats"] = (result == 0)
        except:
            status["nats"] = False
        
        return status
    
    # ==================== ЛАБОРАТОРИЯ ====================
    
    def lab_assemble(self, description):
        """Собрать конвейер из описания"""
        services = self.get_services_list()
        ontology_summary = {k: str(v)[:200] for k, v in self.ontology.items()}
        
        prompt = f"""Ты — главный инженер лаборатории. У тебя есть:

1. Система HiveMind с сервисами: {services}
2. Онтология Astro: {json.dumps(ontology_summary, indent=2, ensure_ascii=False)[:500]}...

Задача: собрать конвейер для: {description}

Ответь в формате:
## 📋 ПЛАН СБОРКИ

### 1. Существующие компоненты
(какие сервисы можно использовать)

### 2. Недостающие компоненты
(чего не хватает)

### 3. Предложения по созданию
(какие сервисы нужно разработать)

### 4. Схема потоков данных
(как данные движутся между компонентами)

### 5. Оценка сложности
(сколько времени займёт)
"""
        return self.ask_ollama(prompt, temperature=0.3, max_tokens=2000)
    
    def lab_diagnose(self, target):
        """Диагностика системы"""
        if target == "hivemind":
            status = self.check_hivemind_status()
            
            # Проверим наличие критических сервисов
            prompt = f"""Ты — главный диагност лаборатории. 

Статус HiveMind:
{json.dumps(status, indent=2, ensure_ascii=False)}

Также знаю, что в идеальной архитектуре должны быть:
- classifier (есть)
- embedder (нет)
- linker (нет)
- api-gateway (должен быть)
- ui (должен быть)

Проанализируй:
1. Что работает?
2. Что не работает?
3. Что отсутствует?
4. Предложи план починки/доработки
5. Приоритеты (что делать в первую очередь)

Ответь подробно, по-русски, с эмодзи для наглядности.
"""
            return self.ask_ollama(prompt, temperature=0.3, max_tokens=2000)
        
        elif target == "astro":
            if not self.ontology:
                return "Онтология Astro не загружена"
            
            prompt = f"""Ты — главный диагност лаборатории.

Онтология Astro содержит:
{json.dumps(list(self.ontology.keys()), indent=2, ensure_ascii=False)}

Проанализируй:
1. Полнота онтологии (каких сущностей не хватает?)
2. Связи между сущностями (видны ли они?)
3. Готовность к интеграции с HiveMind
4. Предложения по доработке

Ответь подробно.
"""
            return self.ask_ollama(prompt, temperature=0.3)
        
        else:
            return f"Неизвестная цель диагностики: {target}. Доступно: hivemind, astro"
    
    def lab_integrate(self, target):
        """Интеграция компонентов"""
        if target == "astro-hivemind":
            if not self.ontology:
                return "Онтология Astro не загружена"
            
            services = self.get_services_list()
            
            prompt = f"""Ты — главный архитектор лаборатории.

Задача: интегрировать Astro и HiveMind.

Что есть:
1. Astro/ontology: {json.dumps(list(self.ontology.keys()), indent=2, ensure_ascii=False)}
2. HiveMind сервисы: {services}

Предложи детальный план интеграции:

## 🔗 ИНТЕГРАЦИЯ ASTRO → HIVEMIND

### 1. Новые сервисы
(какие сервисы нужно создать для работы с онтологией)

### 2. Доработка существующих
(какие существующие сервисы нужно изменить)

### 3. Контракты
(какие NATS-каналы добавить, какие API-эндпоинты)

### 4. Данные
(как хранить акторы, сферы, цели в БД)

### 5. Примеры использования
(3 примера, как это будет работать)

### 6. Оценка трудоёмкости
(по пунктам, в человеко-днях)
"""
            return self.ask_ollama(prompt, temperature=0.3, max_tokens=2500)
        
        else:
            return f"Неизвестная цель интеграции: {target}. Доступно: astro-hivemind"
    
    def lab_command(self, task):
        """Универсальная лаборатория — понимает любые запросы"""
        
        # Убираем "/lab" из начала
        command = task[4:].strip()
        
        # Сначала проверяем известные команды
        if "диагностика hivemind" in command:
            return self.lab_diagnose("hivemind")
        elif "диагностика astro" in command:
            return self.lab_diagnose("astro")
        elif "сборка" in command:
            # Извлекаем описание после "сборка"
            desc = command[command.find("сборка") + len("сборка"):].strip()
            if not desc:
                desc = "общий конвейер обработки документов"
            return self.lab_assemble(desc)
        elif "интеграция" in command and "astro" in command and "hivemind" in command:
            return self.lab_integrate("astro-hivemind")
        
        # Если не похоже на известные команды — спрашиваем LLM
        prompt = f"""Ты — главный инженер лаборатории. У тебя есть доступ к:

    1. Системе HiveMind (статус: {json.dumps(self.check_hivemind_status(), indent=2, ensure_ascii=False)})
    2. Онтологии Astro (содержит: {list(self.ontology.keys())})
    3. Файловой системе (проект: {self.project_dir})

    Запрос пользователя: {command}

    Ответь подробно, по-русски. Если нужно выполнить какие-то действия — опиши их.
    """
        return self.ask_ollama(prompt, temperature=0.3, max_tokens=2000)
    
    # ==================== ОСНОВНОЙ ЦИКЛ ОБРАБОТКИ ====================
    
    def process_task(self, task):
        """Основной обработчик задач"""
        
        # ===== ПОИСК ПО ПАМЯТИ =====
        if any(word in task.lower() for word in ['помнишь', 'что я спрашивал', 'найди в истории', 'что мы обсуждали']):
            results = self.search_memory(task)
            if results:
                print("🔍 Нашёл в памяти:")
                for r in results:
                    print(f"  [{r['type']}] {r.get('timestamp', '')[:10]}: {r.get('content', r.get('file', ''))}")
            else:
                print("Ничего не нашёл в памяти")
            return
        
        # ===== ЕСТЕСТВЕННЫЙ ЯЗЫК ДЛЯ ПРОСМОТРА ФАЙЛОВ =====
        if any(word in task.lower() for word in ['посмотри', 'найди', 'где', 'покажи', 'что в папке', 'какие файлы']):
            path_match = re.search(r'[~/][\w/.-]*', task)
            if path_match:
                path = path_match.group().strip()
                print(self.handle_file_request(path))
            else:
                print("Где именно смотреть? Укажи путь или используй /files")
            return
        
        # ===== КОМАНДЫ =====
        if task == "/help":
            print("""
Доступные команды:
  /help                 - эта справка
  /files                - показать файлы в проекте
  /read <файл>          - прочитать файл
  /write <файл>         - создать/перезаписать файл
  /append <файл>        - добавить текст в конец файла
  /del <файл>           - удалить файл
  /mkdir <папка>        - создать папку
  /ask <вопрос>         - задать вопрос локальной модели
  /code <описание>      - сгенерировать и сохранить код
  /analyze <файл>       - проанализировать файл
  /remember <текст>     - сохранить в память
  /search <запрос>      - поиск по памяти
  /lab ...              - лаборатория (сборка/диагностика/интеграция)
  /hivemind status      - статус HiveMind
  /exit                  - выход
            """)
            return
        
        elif task == "/files":
            print(self.list_files())
            return
        
        elif task.startswith("/read "):
            filename = task[6:].strip()
            print(self.read_file(filename))
            return
        
        elif task.startswith("/write "):
            filename = task[7:].strip()
            print(f"Введите содержимое файла {filename} (пустая строка + Enter для завершения):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            content = "\n".join(lines)
            print(self.write_file(filename, content))
            return
        
        elif task.startswith("/append "):
            filename = task[8:].strip()
            print(f"Введите текст для добавления в {filename} (пустая строка + Enter для завершения):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            content = "\n".join(lines)
            full_path = self.work_dir / filename
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content + "\n")
            print(f"Текст добавлен в {filename}")
            return
        
        elif task.startswith("/del "):
            filename = task[5:].strip()
            full_path = self.work_dir / filename
            if full_path.exists():
                if full_path.is_file():
                    confirm = input(f"Удалить {filename}? (y/n): ")
                    if confirm.lower() in ['y', 'yes', 'да']:
                        full_path.unlink()
                        print(f"Файл {filename} удалён")
                else:
                    print(f"{filename} — это папка, используйте /rmdir (пока не реализовано)")
            else:
                print(f"Файл {filename} не найден")
            return
        
        elif task.startswith("/mkdir "):
            dirname = task[7:].strip()
            full_path = self.work_dir / dirname
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Папка {dirname} создана")
            return
        
        elif task.startswith("/ask "):
            question = task[5:].strip()
            print(f"🤔 Думаю...")
            response = self.ask_ollama(question)
            print("\n" + "="*50)
            print(response)
            print("="*50)
            
            save = input("Сохранить ответ? (y/n): ").lower()
            if save in ['y', 'yes', 'да']:
                filename = input("Имя файла (Enter = answer.txt): ").strip()
                if not filename:
                    filename = f"answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                self.write_file(filename, f"Вопрос: {question}\n\n{response}")
                print(f"Ответ сохранён в {filename}")
            
            self.remember_query(question, response)
            return
        
        elif task.startswith("/code "):
            description = task[6:].strip()
            print(f"💻 Генерирую код для: {description}...")
            
            prompt = f"""Напиши код на Python для задачи: {description}
Только код, без объяснений. Если нужно несколько файлов, укажи это в комментариях.
Код должен быть готов к запуску."""
            
            code = self.ask_ollama(prompt, temperature=0.3, max_tokens=2000)
            
            # Извлекаем код из markdown-блоков
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            
            filename = input("Имя файла для сохранения (Enter = generated_code.py): ").strip()
            if not filename:
                filename = f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            
            self.write_file(filename, code.strip())
            print(f"Код сохранён в {filename}")
            
            run = input("Запустить код? (y/n): ").lower()
            if run in ['y', 'yes', 'да']:
                print("\n" + "="*50)
                print("РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ:")
                print("="*50)
                try:
                    result = subprocess.run(
                        ["python", str(self.work_dir / filename)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    print(result.stdout)
                    if result.stderr:
                        print("ОШИБКИ:")
                        print(result.stderr)
                except subprocess.TimeoutExpired:
                    print("⏱️ Превышено время выполнения (10 сек)")
                except Exception as e:
                    print(f"Ошибка запуска: {e}")
                print("="*50)
            return
        
        elif task.startswith("/analyze "):
            filename = task[9:].strip()
            full_path = self.work_dir / filename
            if not full_path.exists():
                print(f"Файл {filename} не найден")
                return
            
            print(f"🔬 Анализирую {filename}...")
            analysis = self.analyze_content(filename)
            
            if "error" in analysis:
                print(f"❌ Ошибка: {analysis['error']}")
                if "raw" in analysis:
                    print("\nСырой ответ модели:")
                    print(analysis["raw"])
            else:
                print("\n📊 РЕЗУЛЬТАТ АНАЛИЗА:")
                print(f"Тип: {analysis.get('type', '?')} / {analysis.get('subtype', '?')}")
                print(f"Назначение: {analysis.get('purpose', '?')}")
                if analysis.get('key_elements'):
                    print(f"Ключевые элементы: {', '.join(analysis['key_elements'])}")
                if analysis.get('matches_ontology'):
                    print(f"Совпадает с онтологией: {', '.join(analysis['matches_ontology'])}")
                if analysis.get('actions'):
                    print(f"Что можно сделать: {', '.join(analysis['actions'])}")
            
            self.remember_file(filename, analysis)
            return
        
        elif task.startswith("/remember "):
            text = task[10:].strip()
            self.remember_query("manual", text)
            print("✅ Запомнил")
            return
        
        elif task.startswith("/search "):
            query = task[8:].strip()
            results = self.search_memory(query)
            if results:
                print("🔍 Результаты поиска:")
                for r in results:
                    print(f"\n[{r['type']}] {r.get('timestamp', '')[:10]}")
                    if r['type'] == 'query':
                        print(f"  Запрос: {r['content']}")
                        print(f"  Ответ: {r.get('response', '')[:100]}...")
                    else:
                        print(f"  Файл: {r.get('file', '')}")
                        print(f"  Анализ: {r.get('analysis', '')}")
            else:
                print("Ничего не найдено")
            return
        
        elif task.startswith("/lab"):
            result = self.lab_command(task)
            print(result)
            return
        
        elif task == "/hivemind status":
            status = self.check_hivemind_status()
            print("🐝 HIVEMIND STATUS")
            print("="*50)
            print(f"Время: {status['timestamp']}")
            print(f"\n📦 Контейнеры:")
            for s, state in status.get('services', {}).items():
                print(f"  {s}: {state}")
            print(f"\n📨 NATS: {'✅' if status.get('nats') else '❌'}")
            return
        
        elif task == "/exit":
            print("👋 До встречи!")
            self.save_memory()
            sys.exit(0)
        
        # ===== ЕСЛИ НИЧЕГО НЕ ПОДОШЛО =====
        else:
            # Пробуем отправить в LLM как обычный запрос
            print(f"🤔 Думаю над: {task}")
            response = self.ask_ollama(task)
            print("\n" + "="*50)
            print(response)
            print("="*50)
            self.remember_query(task, response)
    
    # ==================== ОСНОВНОЙ ЦИКЛ ====================
    
    def chat_loop(self):
        """Основной цикл общения"""
        print("\n🔬 ЛАБОРАТОРИЯ АКТИВНА")
        print("="*50)
        print("Команды: /help - справка, /lab - лаборатория")
        print("="*50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                self.process_task(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Пока!")
                self.save_memory()
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()

# ==================== ТОЧКА ВХОДА ====================

if __name__ == "__main__":
    import sys
    
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "./ai_workspace"
    
    # Проверка наличия yaml
    try:
        import yaml
    except ImportError:
        print("⚠️ PyYAML не установлен. Установи: pip install pyyaml")
        # Но продолжаем работу
    
    assistant = AIAssistant(project_dir)
    assistant.chat_loop()