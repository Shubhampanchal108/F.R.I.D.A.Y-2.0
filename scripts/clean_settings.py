import os
import re

html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "interface", "index.html")

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace speech rate and pitch keeping spans
content = re.sub(
    r'<span class="setting-name">Speech Rate</span>\s*<span class="setting-desc">Voice playback speed \(<span id="val-speech-rate">185</span> WPM\)</span>',
    '<span class="setting-name">Speech Rate (<span id="val-speech-rate">185</span> WPM)</span>',
    content
)

content = re.sub(
    r'<span class="setting-name">Synthesizer Pitch</span>\s*<span class="setting-desc">Vocal tone frequency \(<span id="val-speech-pitch">50</span>%\)</span>',
    '<span class="setting-name">Synthesizer Pitch (<span id="val-speech-pitch">50</span>%)</span>',
    content
)

# Remove all other setting-desc in view-settings
# Find section#view-settings
start_tag = '<section class="view-pane" id="view-settings">'
end_tag = '</section>'

start_pos = content.find(start_tag)
if start_pos != -1:
    end_pos = content.find(end_tag, start_pos)
    if end_pos != -1:
        settings_html = content[start_pos:end_pos]
        # Remove setting-desc
        settings_html = re.sub(r'\s*<span class="setting-desc">.*?</span>', '', settings_html)
        # Remove section-subtext
        settings_html = re.sub(r'\s*<p class="section-subtext">.*?</p>', '', settings_html)
        # Remove provider-tag
        settings_html = re.sub(r'\s*<span class="provider-tag">.*?</span>', '', settings_html)
        content = content[:start_pos] + settings_html + content[end_pos:]

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Settings HTML cleaned successfully.")

