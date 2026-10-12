
import html
import re
import streamlit.components.v1 as components


def clean_label(value):
    label = re.sub(
        r"[^A-Za-z0-9 ,.!?/-]",
        " ",
        str(value)
    )
    return re.sub(r"\s+", " ", label).strip()[:55] or "Concept"


def to_mermaid(tree):
    lines = [
        "mindmap",
        f"  root(({clean_label(tree['root'])}))"
    ]

    counter = 0

    def add_nodes(nodes, depth):
        nonlocal counter

        for node in nodes[:7]:
            if not isinstance(node, dict):
                continue

            counter += 1
            label = clean_label(node.get("name", "Concept"))

            lines.append(
                f"{'  ' * depth}n{counter}[{label}]"
            )

            if depth < 3 and isinstance(
                node.get("children"), list
            ):
                add_nodes(node["children"], depth + 1)

    add_nodes(tree["children"], 2)
    return "\n".join(lines)


def render_mindmap(tree):
    diagram = to_mermaid(tree)

    components.html(
        f"""
        <html>
        <body style="margin:0;background:#1B2A4A;">
            <pre class="mermaid">{html.escape(diagram)}</pre>

            <script type="module">
                import mermaid from
                'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'dark',
                    securityLevel: 'strict'
                }});

                await mermaid.run({{
                    querySelector: '.mermaid'
                }});
            </script>
        </body>
        </html>
        """,
        height=550,
        scrolling=True
    )

    return diagram
