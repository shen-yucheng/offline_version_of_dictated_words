import pypinyin
import bs4
import re
import pdfkit
import zipfile
import io
import os


def new_tag(html: str):
    return bs4.BeautifulSoup(html, "lxml").contents[0].contents[0].contents[0]


class Text:
    question_soup = None
    answer_soup = None
    question_pdf = None
    answer_pdf = None

    def __init__(self, words_text: str, raw_html: str, title="看音写词",
                 pdfkit_config="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"):
        """
        words_split_by_enter_or_space
        """

        def pinyin(word):
            return " ".join(
                (each_pinyin[0] for each_pinyin in pypinyin.pinyin(word))
            )

        self.title = title
        self.raw_html = raw_html

        # 去除换行符
        self.words_text = re.sub(
            r"\\.",
            " ",
            repr(words_text)[1:-1]
        )
        # 去除多余空格
        self.words_text = re.sub(
            r"\s+",
            " ",
            words_text
        )
        self.pinyin_dict = {each_word: pinyin(each_word) for each_word in self.words_text.split(" ")}

        self.pdfkit_config = pdfkit.configuration(
            wkhtmltopdf=pdfkit_config
        )

    def get_answer_html(self):
        if self.answer_soup is None:
            self.answer_soup = bs4.BeautifulSoup(self.raw_html, "lxml")

            # 添加标题
            self.answer_soup.head.append(
                new_tag(rf"<title>{self.title}</title>")
            )
            self.answer_soup.body.append(
                new_tag(rf"<h1>{self.title}</h1>")
            )

            # 添加每道题
            for each_pinyin in self.pinyin_dict:
                self.answer_soup.body.append(
                    new_tag(
                        rf'<div class="question"><p class="pinyin">{self.pinyin_dict[each_pinyin]}</p><p class="kuohao">（</p><pre class="kuohao answer">{each_pinyin :^{len(each_pinyin) * 2}}</pre><p class="kuohao">）</p></div>'
                    )
                )

        return str(
            self.answer_soup.prettify()
        )

    def get_question_html(self):
        if self.question_soup is None:
            # deepcopy会出错
            self.question_soup = bs4.BeautifulSoup(
                self.get_answer_html(),
                "lxml"
            )

            self.question_soup.append(
                new_tag(
                    r"<style>.answer{color: rgba(0, 0, 0, 0)}</style>"
                )
            )

        return str(
            self.question_soup.prettify()
        )

    def get_answer_pdf(self):
        self.answer_pdf = pdfkit.from_string(
            self.get_answer_html(),
            False,
            configuration=self.pdfkit_config
        )
        return self.answer_pdf

    def get_question_pdf(self):
        self.question_pdf = pdfkit.from_string(
            self.get_question_html(),
            False,
            configuration=self.pdfkit_config
        )
        return self.question_pdf

    def get_zip(self) -> io.BytesIO:
        file = io.BytesIO()
        zip_file = zipfile.ZipFile(
            file,
            "w"
        )

        zip_file.writestr(
            f"{self.title} 答案.html",
            self.get_answer_html()
        )
        zip_file.writestr(
            f"{self.title}.html",
            self.get_question_html()
        )
        zip_file.writestr(
            f"{self.title} 答案.pdf",
            self.get_answer_pdf()
        )
        zip_file.writestr(
            f"{self.title}.pdf",
            self.get_question_pdf()
        )
        zip_file.writestr(
            f"{self.title} 源词.txt",
            self.words_text
        )

        zip_file.close()
        file.seek(0)

        return file

    def write_zip(self, file_name: str):
        open(file_name, "wb").write(
            self.get_zip().getvalue()
        )

    def write_folder(self, folder_name: str):
        os.makedirs(folder_name)

        open(fr"{folder_name}/{self.title} 答案", "wb").write(
            self.get_answer_html()
        )
        open(fr"{folder_name}/{self.title}.html", "wb").write(
            self.get_question_html()
        )
        open(fr"{folder_name}/{self.title} 答案.pdf", "wb").write(
            self.get_answer_pdf()
        )
        open(fr"{folder_name}/{self.title}.pdf", "wb").write(
            self.get_question_pdf()
        )
        open(fr"{folder_name}/{self.title} 原词.txt", "w").write(
            self.words_text
        )
