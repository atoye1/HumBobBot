from typing import Dict, List

import time
import os
import subprocess
import logging
import datetime
from urllib.parse import urlparse, parse_qs

import requests

from bs4 import BeautifulSoup
from database import SessionLocal

# Custom modules
import config
from models import Regulation

# For SQLAlchemy Session type hinting
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Helper type for clarity
RegulationObject = Regulation # Alias for type hinting from models.py

class RegulationPost:
    def __init__(self, post_type, post_title, post_create_date, post_file_url, post_enforce_date, post_next_link) -> None:
        self.type = post_type
        self.title = post_title
        self.create_date = post_create_date
        self.file_url = post_file_url
        self.enforce_date = post_enforce_date
        self.next_link = post_next_link

class RegulationCrawler:
    base_url = config.REGULATION_CRAWLER_BASE_URL
    target_boards = [
        "/homepage/default/board/list.do?conf_no=105&board_no=&category_cd=&menu_no=1001060302",
        "/homepage/default/board/list.do?conf_no=107&board_no=&category_cd=&menu_no=1001060303",
        "/homepage/default/board/list.do?conf_no=106&board_no=&category_cd=&menu_no=1001060301",
    ]

    # Removed class-level db = SessionLocal()
    # The db session will now be injected.

    def __init__(self, db_session: Session) -> None: # db_session is now a required argument
        logger.info("Initializing RegulationCrawler...")
        self.db: Session = db_session # Store the injected session
        self.current_post_info: Dict | None = dict() # Consider if this is still used.
        self.error_list : List[str] = [] # Explicitly type the list elements.
        
        self.hwp5html_available: bool = False
        self.docker_available: bool = False
        self._check_dependencies() # Check dependencies on initialization

    # --- Dependency Check Methods ---
    def _check_dependencies(self) -> None:
        """Checks for hwp5html and Docker availability and sets instance flags."""
        logger.info("Checking for required system dependencies...")
        self._check_hwp5html_availability()
        self._check_docker_availability()

    def _check_hwp5html_availability(self) -> None:
        """Checks for hwp5html and sets self.hwp5html_available."""
        try:
            result = subprocess.run(
                ["hwp5html", "--version"],
                capture_output=True, text=True, timeout=5, check=False
            )
            if result.returncode == 0:
                logger.info(f"hwp5html found: {result.stdout.strip()}")
                self.hwp5html_available = True
            else:
                logger.error(
                    f"hwp5html --version check failed. RC: {result.returncode}. Stderr: {result.stderr}. HWP conversion will be unavailable."
                )
                self.hwp5html_available = False
        except FileNotFoundError:
            logger.error("hwp5html command not found. HWP conversion will be unavailable.")
            self.hwp5html_available = False
        except subprocess.TimeoutExpired:
            logger.error("hwp5html --version command timed out. HWP conversion will be unavailable.")
            self.hwp5html_available = False
        except Exception as e: # Catch any other unexpected error during check
            logger.error(
                f"An unexpected error occurred while checking hwp5html version: {e}", exc_info=True
            )
            self.hwp5html_available = False

    def _check_docker_availability(self) -> None:
        """Checks for Docker and sets self.docker_available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=5, check=False
            )
            if result.returncode == 0:
                logger.info(f"Docker found: {result.stdout.strip()}")
                self.docker_available = True
            else:
                logger.error(
                    f"docker --version check failed. RC: {result.returncode}. Stderr: {result.stderr}. PDF conversion via Docker will be unavailable."
                )
                self.docker_available = False
        except FileNotFoundError:
            logger.error("Docker command not found. PDF conversion via Docker will be unavailable.")
            self.docker_available = False
        except subprocess.TimeoutExpired:
            logger.error("Docker --version command timed out. PDF conversion via Docker will be unavailable.")
            self.docker_available = False
        except Exception as e: # Catch any other unexpected error during check
            logger.error(
                f"An unexpected error occurred while checking Docker version: {e}", exc_info=True
            )
            self.docker_available = False

    # --- Filename and Path Generation Helpers ---

    def _get_file_extension_from_url(
        self, regulation_title: str, file_url: str
    ) -> str:
        """
        Extracts the file extension from the 'file_name_origin' query parameter in the URL.
        Example: "http://...&file_name_origin=example.pdf" -> "pdf"
        """
        try:
            query_params = parse_qs(urlparse(file_url).query)
            file_name_origin_list = query_params.get("file_name_origin")
            if not file_name_origin_list or not file_name_origin_list[0]:
                logger.warning(
                    f"Could not determine original filename from URL: {file_url} for '{regulation_title}'"
                )
                return "bin"  # Default extension if not found

            original_filename = file_name_origin_list[0]
            return (
                original_filename.split(".")[-1].lower()
                if "." in original_filename
                else "bin"
            )
        except Exception as e:
            logger.error(
                f"Error parsing file URL's query string for extension ('{regulation_title}'): {file_url} - {e}",
                exc_info=True,
            )
            return "bin"

    def _generate_download_filename(
        self, regulation: RegulationObject, file_ext: str
    ) -> str:
        """Generates a standardized filename for downloading."""
        # Sanitize title for use in filename (very basic sanitization)
        sanitized_title = regulation.title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        create_date_str = (
            regulation.create_date.strftime("%Y-%m-%d")
            if isinstance(regulation.create_date, (datetime.datetime, datetime.date))
            else str(regulation.create_date) # Fallback if not a date/datetime object
        )
        return f"[{regulation.type}]{sanitized_title}_{create_date_str}.{file_ext}"

    def _generate_html_output_dirname(
        self, downloaded_filename: str, file_ext: str
    ) -> str:
        """
        Generates the directory name (under REGULATION_HTML_DIR) for HTML output,
        from the downloaded filename by removing its extension.
        """
        return downloaded_filename.replace(f".{file_ext}", "")

    # --- Post Handling and Crawling Methods ---

    def handle_post(self, post_link: str) -> RegulationPost:
        logger.debug(f"Handling post: {post_link}")
        try:
            post_html_response = requests.get(
                config.REGULATION_CRAWLER_BASE_URL + post_link, timeout=10
            )
            post_html_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch post HTML for link {post_link}: {e}", exc_info=True)
            # Depending on desired behavior, could return None or raise an exception
            raise # Re-raise for now, as the caller might need to know
            
        post_soup = BeautifulSoup(post_html_response.content, 'lxml')
        
        title_elem = post_soup.select_one('div.board-view-title')
        if not title_elem:
            logger.error(f"Could not find title element 'div.board-view-title' for post: {post_link}")
            # Handle error appropriately, maybe raise an exception or return a default/empty RegulationPost
            raise ValueError(f"Missing title element in post: {post_link}")
        post_text = title_elem.text

        next_post_link_elem = post_soup.select_one("li.li-prev a")
        post_next_link = (
            next_post_link_elem.get("href") if next_post_link_elem else None
        )
        logger.debug(f"Next post link: {post_next_link}")

        # Edge case handling for post text possibly missing the category prefix.
        # Assumes post_text is expected to be like: "[Category] Title\nMore Info\nDate..."
        if "정관" in post_text and not post_text.startswith("정관"):
            post_text = "정관" + post_text
        elif "조례" in post_text and not post_text.startswith("조례"):
            post_text = "조례" + post_text

        # Expected structure of post_text after above normalization:
        # line 0: "[Category] Title" or "Category Title" (if brackets are inconsistent)
        # line 1: (possibly empty or more title parts)
        # line 2: (possibly some other info)
        # line 3: "YYYY-MM-DD" (Create Date)
        # This parsing is fragile and depends heavily on consistent formatting in `div.board-view-title`.
        post_info_list = [
            i.strip() for i in post_text.replace("\t", "").split("\n") if i.strip() != ""
        ]
        
        if len(post_info_list) < 4:
            logger.error(f"Post text for {post_link} has fewer lines than expected after parsing. Parsed list: {post_info_list}")
            # This indicates a parsing problem or unexpected format.
            # Depending on strictness, could raise an error or try to proceed with defaults.
            raise ValueError(f"Unexpected post text format for {post_link}")

        post_type = post_info_list[0].replace("[", "").replace("]", "")
        post_title = post_info_list[1]

        # Further attempts to normalize type and title
        if "[내규]" in post_title:
            post_type = "내규"
            post_title = post_title.replace("[내규]", "").strip()
        elif post_type not in ["정관", "조례", "내규", "시행세칙", "지침"] and post_title.startswith(f"[{post_type}]"): # Example if type is in title
             post_title = post_title.replace(f"[{post_type}]", "").strip()


        post_create_date_str = post_info_list[3]
        try:
            post_create_date = datetime.datetime.strptime(post_create_date_str, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Could not parse create date '{post_create_date_str}' for post '{post_title}': {e}")
            # Decide on fallback: raise error, or use a default date? For now, re-raise.
            raise ValueError(f"Invalid create date format for {post_title}: {post_create_date_str}") from e
            
        logger.info(
            f"Processing regulation: Type='{post_type}', Title='{post_title}', CreateDate='{post_create_date.strftime('%Y-%m-%d')}'"
        )

        file_url_elem = post_soup.select_one("ul.board-view-filelist a")
        if file_url_elem:
            post_file_url = file_url_elem.get('href')
            logger.debug(f"Found file URL: {post_file_url}")
        else:
            post_file_url = None
            logger.warning(f"No file URL found for post: {post_title}")

        post_enforce_date = None
        try:
            # Stricter selection for enforcement date to avoid accidental matches
            enforce_date_elem_container = post_soup.select_one('div#boardContents')
            if enforce_date_elem_container:
                enforce_date_text_full = enforce_date_elem_container.text.strip()
                # Example: "시행일 :2023년01월01일" or "시행일: 2023. 1. 1." - needs robust parsing
                if ':' in enforce_date_text_full:
                    post_enforce_date_text = enforce_date_text_full.split(':', 1)[1].strip().replace(' ', '')
                    # Normalize various date formats if possible
                    post_enforce_date_text = (
                        post_enforce_date_text.replace("년", "-")
                        .replace("월", "-")
                        .replace("일", "")
                    )
                    if post_enforce_date_text.endswith("."):  # Handle "YYYY-MM-DD."
                        post_enforce_date_text = post_enforce_date_text[:-1]
                    post_enforce_date = datetime.datetime.strptime(
                        post_enforce_date_text, "%Y-%m-%d"
                    )
                    logger.debug(
                        f"Found enforcement date: {post_enforce_date.strftime('%Y-%m-%d')}"
                    )
            else:
                logger.warning(
                    f"Enforcement date container 'div#boardContents' not found for post: {post_title}"
                )
        except Exception as e:
            logger.warning(
                f"Could not parse enforcement date for post '{post_title}'. Raw text: '{enforce_date_text_full if 'enforce_date_text_full' in locals() else 'N/A'}'. Error: {e}",
                exc_info=True,
            )
            post_enforce_date = None # Ensure it's None if parsing fails

        return RegulationPost(
            post_type,
            post_title,
            post_create_date,
            post_file_url,
            post_enforce_date,
            post_next_link,
        )

    def crawl(self) -> None: # Major method, PEP8 line breaks for readability
        logger.info("Starting regulation crawl process...")
        try:
            for board_url_path in self.target_boards:
                logger.info(f"Crawling board: {board_url_path}")
                try:
                    board_html_response = requests.get(
                        config.REGULATION_CRAWLER_BASE_URL + board_url_path, timeout=10
                    )
                    board_html_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"Failed to fetch board HTML for {board_url_path}: {e}",
                        exc_info=True,
                    )
                    continue  # Skip to next board

                board_soup = BeautifulSoup(board_html_response.content, "lxml")

                first_post_row = board_soup.select_one(
                    "table.basic-list-table tbody tr"
                )  # More specific
                if not first_post_row:
                    logger.warning(f"No posts found on board: {board_url_path}")
                    continue  # Skip to next board
                
                next_link_elem = first_post_row.select_one("a")
                if not next_link_elem:
                    logger.warning(
                        f"No link found in the first post of board: {board_url_path}"
                    )
                    continue  # Skip to next board
                next_link = next_link_elem.get("href")

                while next_link:
                    try:
                        post = self.handle_post(next_link)
                    except Exception as e:  
                        logger.error(
                            f"Failed to handle post with link {next_link}. Error: {e}",
                            exc_info=True,
                        )
                        break # If handle_post fails critically, break from this board's processing.

                    regulation = (
                        self.db.query(Regulation) # type: ignore
                        .filter_by(title=post.title, type=post.type)
                        .first()
                    )

                    if not regulation:
                        logger.info(
                            f"Regulation '{post.title}' (Type: {post.type}) not found in DB. Adding new."
                        )
                        regulation = Regulation(
                            title=post.title,
                            type=post.type,
                            create_date=post.create_date,
                            update_date=post.create_date, 
                            enforce_date=post.enforce_date,
                            file_url=post.file_url,
                            html_url=None,
                        )
                        self.db.add(regulation) # type: ignore
                        self.db.commit() # type: ignore
                        logger.info(f"Added new regulation: {post.title}")
                    elif post.create_date and regulation.create_date < post.create_date:
                        logger.info(
                            f"Regulation '{post.title}' (Type: {post.type}) exists but is outdated. Updating."
                        )
                        regulation.create_date = post.create_date
                        regulation.update_date = datetime.datetime.now()
                        regulation.enforce_date = post.enforce_date
                        regulation.file_url = post.file_url
                        regulation.html_url = None  # Reset html_url
                        self.db.commit() # type: ignore
                        logger.info(f"Updated regulation: {post.title}")
                    else:
                        logger.info(
                            f"Regulation '{post.title}' (Type: {post.type}) is up-to-date or newer in DB. Skipping."
                        )
                    next_link = post.next_link
            logger.info("Regulation crawl process finished.")
        except Exception as e:
            logger.critical(
                f"A critical error occurred during the regulation crawl: {e}",
                exc_info=True,
            )
        finally:
            # Session closing is now handled by the caller of crawl()
            logger.info("Crawl method finished. DB session management is external.")
            # self.db.close() # type: ignore # REMOVED

    # --- File Processing Methods (Refactored) ---

    def _get_regulations_needing_html_conversion(self) -> List[RegulationObject]:
        """Queries the database for regulations where html_url is None."""
        logger.info("Fetching regulations that need HTML conversion.")
        try:
            targets = (
                self.db.query(Regulation).filter(Regulation.html_url == None).all() # type: ignore
            )
            logger.info(f"Found {len(targets)} regulations for HTML conversion.")
            return targets
        except Exception as e:
            logger.error(
                f"Database error while fetching regulations for conversion: {e}",
                exc_info=True,
            )
            return []

    def _download_regulation_file(
        self, regulation: RegulationObject
    ) -> str | None:
        """
        Downloads the file for a given regulation.
        Returns the full path to the downloaded file, or None on failure.
        """
        if not regulation.file_url:
            logger.warning(
                f"Skipping download for '{regulation.title}': No file URL provided."
            )
            return None

        file_ext = self._get_file_extension_from_url(
            regulation.title, regulation.file_url
        )
        downloaded_filename = self._generate_download_filename(regulation, file_ext)
        full_download_path = os.path.join(config.DOWNLOAD_DIR, downloaded_filename)

        logger.info(
            f"Downloading file: {downloaded_filename} for regulation '{regulation.title}' from {config.REGULATION_CRAWLER_BASE_URL + regulation.file_url}"
        )
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

        try:
            res = requests.get(
                config.REGULATION_CRAWLER_BASE_URL + regulation.file_url, timeout=30
            )
            res.raise_for_status()
            with open(full_download_path, 'wb') as f:
                f.write(res.content)
            logger.info(f"Successfully downloaded {downloaded_filename} to {full_download_path}")
            return full_download_path
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error downloading file {downloaded_filename} for '{regulation.title}': {e}",
                exc_info=True,
            )
            self.error_list.append(
                f"{regulation.title} (ID: {regulation.id}) - HTTP download error: {e.response.status_code if e.response else 'Unknown'}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request exception downloading file {downloaded_filename} for '{regulation.title}': {e}",
                exc_info=True,
            )
            self.error_list.append(
                f"{regulation.title} (ID: {regulation.id}) - Download request error"
            )
        except IOError as e:
            logger.error(
                f"IOError saving file {downloaded_filename} to {full_download_path} for '{regulation.title}': {e}",
                exc_info=True,
            )
            self.error_list.append(
                f"{regulation.title} (ID: {regulation.id}) - File save error"
            )
        return None

    def _convert_file_to_html_format(
        self,
        regulation: RegulationObject,
        downloaded_file_path: str,
        downloaded_filename: str,
    ) -> str | None:
        """
        Converts the downloaded file to HTML.
        Returns a relative path to the main HTML file (e.g., 'dirname/index.html')
        on success, else None.
        The relative path is based on config.REGULATION_HTML_DIR.
        """
        file_ext = downloaded_filename.split('.')[-1].lower()
        html_output_dirname = self._generate_html_output_dirname(downloaded_filename, file_ext)
        # Absolute path to the output directory for this specific file's HTML assets
        absolute_html_output_path = os.path.join(
            config.REGULATION_HTML_DIR, html_output_dirname
        )
        os.makedirs(absolute_html_output_path, exist_ok=True)

        logger.info(
            f"Converting file: {downloaded_filename} for '{regulation.title}' to HTML. Output dir: {absolute_html_output_path}"
        )

        main_html_filename = None  # To store the name of the primary HTML file

        if "hwp" == file_ext:
            if not self.hwp5html_available:
                logger.warning(
                    f"HWP conversion skipped for '{downloaded_filename}' as hwp5html is not available."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - Skipped: hwp5html unavailable"
                )
                return None
            try:
                cmd = [
                    "hwp5html",
                    "--output",
                    absolute_html_output_path,
                    downloaded_file_path,
                ]
                logger.debug(f"Executing HWP conversion: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60, check=False
                )
                if result.returncode != 0:
                    logger.error(
                        f"hwp5html conversion failed for {downloaded_filename}. RC: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
                    )
                    self.error_list.append(
                        f"{regulation.title} (ID: {regulation.id}) - HWP conversion error (RC: {result.returncode})"
                    )
                else:
                    logger.info(
                        f"hwp5html conversion successful for {downloaded_filename}."
                    )
                    main_html_filename = "index.html"  # hwp5html default output
            except FileNotFoundError:
                logger.error("hwp5html command not found during conversion.")
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - hwp5html not found"
                )
            except subprocess.TimeoutExpired:
                logger.error(
                    f"hwp5html conversion timed out for {downloaded_filename}."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - HWP conversion timeout"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during HWP conversion for {downloaded_filename}: {e}",
                    exc_info=True,
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - HWP unexpected error"
                )

        elif "pdf" == file_ext:
            if not self.docker_available:
                logger.warning(
                    f"PDF conversion skipped for '{downloaded_filename}' as Docker is not available."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - Skipped: Docker unavailable"
                )
                return None
            try:
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{config.DOWNLOAD_DIR}:/pdf_input:ro",
                    "-v",
                    f"{absolute_html_output_path}:/pdf_output",
                    "-w",
                    "/pdf_input",
                    "pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-alpine-3.12.0-x86_64",
                    downloaded_filename,
                    "--dest-dir",
                    "/pdf_output",
                ]
                logger.debug(f"Executing PDF conversion: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120, check=False
                )
                if result.returncode != 0:
                    if (
                        "docker: command not found" in result.stderr
                        or "Is the docker daemon running?" in result.stderr
                    ):
                        logger.error(
                            f"Docker command failed for {downloaded_filename}. Stderr: {result.stderr}"
                        )
                        self.error_list.append(
                            f"{regulation.title} (ID: {regulation.id}) - Docker command/daemon error"
                        )
                    else:
                        logger.error(
                            f"pdf2htmlex failed for {downloaded_filename}. RC: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
                        )
                        self.error_list.append(
                            f"{regulation.title} (ID: {regulation.id}) - PDF conversion error (RC: {result.returncode})"
                        )
                else:
                    logger.info(
                        f"pdf2htmlex conversion successful for {downloaded_filename}."
                    )
                    main_html_filename = downloaded_filename.replace(
                        f".{file_ext}", ".html"
                    )
            except FileNotFoundError:
                logger.error("Docker command not found. Ensure Docker is installed.")
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - Docker command not found"
                )
            except subprocess.TimeoutExpired:
                logger.error(
                    f"pdf2htmlex conversion timed out for {downloaded_filename}."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - PDF conversion timeout"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during PDF conversion for {downloaded_filename}: {e}",
                    exc_info=True,
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - PDF unexpected error"
                )
        else:
            logger.warning(
                f"Unsupported file type '{file_ext}' for conversion: {downloaded_filename}"
            )
            self.error_list.append(
                f"{regulation.title} (ID: {regulation.id}) - Unsupported file type: {file_ext}"
            )

        if main_html_filename:
            # Return path relative to config.REGULATION_HTML_DIR
            return os.path.join(html_output_dirname, main_html_filename)
        return None

    def _update_db_html_url(
        self, regulation: RegulationObject, html_file_rel_path: str
    ) -> None:
        """Updates the html_url in the database for the given regulation."""
        try:
            logger.info(
                f"Updating database: html_url='{html_file_rel_path}' for regulation ID {regulation.id} ('{regulation.title}')"
            )
            regulation.html_url = html_file_rel_path
            regulation.update_date = datetime.datetime.now()  # Also update the timestamp
            self.db.commit()  # type: ignore
            logger.info(
                f"Successfully updated html_url for regulation ID {regulation.id}."
            )
        except Exception as e:
            logger.error(
                f"Database error while updating html_url for regulation ID {regulation.id}: {e}",
                exc_info=True,
            )
            self.db.rollback()  # type: ignore
            self.error_list.append(
                f"{regulation.title} (ID: {regulation.id}) - DB update error for html_url"
            )

    def _remove_downloaded_original(self, downloaded_file_path: str) -> None:
        """
        Removes the original downloaded file if KEEP_DOWNLOADED_ORIGINALS is False.
        """
        if not config.KEEP_DOWNLOADED_ORIGINALS:
            try:
            logger.info(
                f"Removing original downloaded file: {downloaded_file_path}"
            )
                os.remove(downloaded_file_path)
                logger.info(f"Successfully removed: {downloaded_file_path}")
            except OSError as e:
            logger.error(
                f"Error removing original file {downloaded_file_path}: {e}",
                exc_info=True,
            )
        else:
            logger.debug(
                f"KEEP_DOWNLOADED_ORIGINALS is True. Retaining file: {downloaded_file_path}"
            )

    def _process_single_regulation_file(
        self, regulation: RegulationObject
    ) -> None:
        """
        Handles download, conversion, DB update, and cleanup for a single regulation.
        """
        logger.info(
            f"Processing file for regulation: '{regulation.title}' (ID: {regulation.id})"
        )

        downloaded_file_path = None
        try:
            if not regulation.file_url:
                logger.warning(
                    f"Skipping processing for '{regulation.title}' (ID: {regulation.id}): No file_url."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - No file_url for processing"
                )
                return

            # 1. Download (uses its own internal filename generation based on regulation object)
            downloaded_file_path = self._download_regulation_file(regulation)

            if not downloaded_file_path or not os.path.exists(downloaded_file_path):
                logger.error(
                    f"Download failed or file not found for '{regulation.title}'. Path: {downloaded_file_path}"
                )
                if not any(f"{regulation.title} (ID: {regulation.id})" in err for err in self.error_list):
                    self.error_list.append(
                        f"{regulation.title} (ID: {regulation.id}) - Download failed/file missing"
                    )
                return

            # 2. Convert
            actual_downloaded_filename = os.path.basename(downloaded_file_path)
            relative_html_path = self._convert_file_to_html_format(
                regulation, downloaded_file_path, actual_downloaded_filename
            )

            if not relative_html_path:
                logger.error(f"HTML conversion failed for '{regulation.title}'.")
                return

            # 3. Update Database
            self._update_db_html_url(regulation, relative_html_path)

            # 4. Remove original downloaded file (conditionally)
            if not any(f"{regulation.title} (ID: {regulation.id}) - DB update error" in err for err in self.error_list):
                self._remove_downloaded_original(downloaded_file_path)
            else:
                logger.warning(
                    f"Skipping removal of {downloaded_file_path} due to DB update error for '{regulation.title}'."
                )

        except Exception as e:
            logger.error(
                f"Unexpected error processing regulation '{regulation.title}' (ID: {regulation.id}): {e}",
                exc_info=True,
            )
            if not any(f"{regulation.title} (ID: {regulation.id})" in err for err in self.error_list):
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - Unexpected processing error: {str(e)[:100]}"
                )

    def handle_file_process(self) -> None:
        """
        Orchestrates the process of converting regulation files to HTML.
        - Fetches regulations needing conversion.
        - For each, downloads, converts, updates DB, and optionally cleans up.
        """
        logger.info("Starting file processing batch.")
        self.error_list = []  # Reset error list for this batch

        # Log the availability status of dependencies (checked during __init__)
        logger.info(f"Dependency status: hwp5html available - {self.hwp5html_available}, Docker available - {self.docker_available}")

        regulations_to_process = self._get_regulations_needing_html_conversion()

        if not regulations_to_process:
            logger.info("No regulations found needing HTML conversion.")
            return

        for regulation in regulations_to_process:
            if not regulation.file_url:
                logger.warning(
                    f"Skipping '{regulation.title}' (ID: {regulation.id}) at main loop start: No file_url."
                )
                self.error_list.append(
                    f"{regulation.title} (ID: {regulation.id}) - Skipped: No file_url"
                )
                continue
            self._process_single_regulation_file(regulation)

        if self.error_list:
            logger.error(
                f"Finished file processing batch with errors. {len(self.error_list)} file(s) failed. See errors below:"
            )
            for error_detail in self.error_list:
                logger.error(f" - {error_detail}")
        else:
            logger.info(
                "Finished file processing batch successfully. All files processed without critical errors."
            )

    # --- Original Methods (to be removed or fully replaced by refactored ones) ---

    def check_file_exists(self) -> None:  # This method was not implemented.
        logger.warning(
            "check_file_exists method was called but is not implemented."
        )
        pass

    # download_file is now _download_regulation_file
    # update_html_url is now _update_db_html_url (and takes relative path)
    # convert_file_to_html is now _convert_file_to_html_format

if __name__ == "__main__":
    logger.info("RegulationCrawler script started directly.")
    # It's good practice to manage the DB session explicitly when running standalone.
    db_session_for_script: Session | None = None # Ensure it's defined for finally block
    logger.info("RegulationCrawler script started directly.")
    try:
        db_session_for_script = SessionLocal()
        # __init__ will call _check_dependencies()
        # Pass the created session to the constructor
        crawler = RegulationCrawler(db_session=db_session_for_script)
        
        # Example usage:
        # To run crawl:
        # crawler.crawl() 
        
        # To run file processing:
        crawler.handle_file_process() # This method uses self.db internally

    except Exception as e:
        logger.critical(f"Unhandled exception in RegulationCrawler __main__: {e}", exc_info=True)
    finally:
        if 'crawler' in locals() and crawler.error_list: # Check if crawler was instantiated
             logger.error(f"RegulationCrawler finished with errors: {crawler.error_list}")
        else:
             logger.info("RegulationCrawler finished processing or was not fully initialized.")
        
        if db_session_for_script:
            logger.info("Closing DB session for script from __main__.")
            db_session_for_script.close()
        logger.info("RegulationCrawler script finished.")