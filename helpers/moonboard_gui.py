"""Graphical user interface for the moonboard."""

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


def visualise_route(holds, grade="", year="2017", board="moonboard") -> None:
    """Visualise a route on the moonboard."""
    img = Image.open(f"../media/boards/{year}_{board}.png")
    font = ImageFont.truetype("../media/fonts/montserrat_grade_font.ttf", 32)
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), grade, fill=(0, 0, 255), font=font)
    # TODO add color to first 2 and last holds
    for (x, y) in holds:
        x = 93 + 50 * x
        y = 1000 - (64 + 50 * y)
        draw.ellipse((x - 25, y - 25, x + 25, y + 25), fill=None, outline=(0, 0, 255), width=5)
    plt.imshow(img)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.show()


def main() -> None:
    """Main function, used for testing."""
    visualise_route([[0, 0], [5, 1], [4, 7], [6, 11], [1, 15], [3, 17]], "7B+")


if __name__ == "__main__":
    main()
