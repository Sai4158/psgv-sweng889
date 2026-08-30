from pathlib import Path
from wordcloud import WordCloud


def load_report(file_path):
    return Path(file_path).read_text(encoding="utf-8")


def clean_text(text):
    return text.lower()


def generate_wordcloud(text, output_path):
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white"
    ).generate(text)

    wordcloud.to_file(output_path)


def main():
    input_file = "report.txt"
    output_file = "output/wordcloud.png"

    Path("output").mkdir(exist_ok=True)

    text = load_report(input_file)
    text = clean_text(text)

    generate_wordcloud(text, output_file)

    print(f"Word cloud created: {output_file}")


if __name__ == "__main__":
    main()
