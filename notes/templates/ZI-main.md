{# version: 3.5 -#}
---
citekey: {{citekey}}
aliases:
- "{%- if creators -%}
        {{creators[0].lastName}}
        {%- if creators|length == 2 %} & {{creators[1].lastName}}{% endif -%}
        {%- if creators|length > 2 %} et al.{% endif -%}
    {%- endif -%}
    {%- if date %} ({{date | format("YYYY")}}){% endif -%} 
    {%- if shortTitle %} {{shortTitle | safe}} {%- else %} {{title | safe}} {%- endif -%}"{% if itemType == "bookSection" %}
book-title: "{{bookTitle | replace('"',"'")}}"{% endif %}
title: "{{title | replace('"',"'")}}"
{%- set camelRegex = r/([a-z])([A-Z])/g %}
{%- for type, creators in creators | groupby("creatorType") %} 
{% if creators.length > 1 %}{{type | replace(camelRegex, "$1 $2") | lower | trim}}s:{%- for creator in creators %}{% if creator.name %}
- {{creator.name}}{% else%}
- {{creator.firstName}} {{creator.lastName}} {% endif %}{%- endfor %} {% else -%}
{{type | replace(camelRegex, "$1-$2") | lower | trim}}:{%- for creator in creators %}{% if creator.name %} "{{creator.name}}"{% else%} "{{creator.firstName}} {{creator.lastName}}"{% endif -%}{%- endfor -%}{% endif -%}{% endfor %}
year: {% if date %}{{date | format("YYYY")}}{% endif %}
item-type: {{itemType | replace(camelRegex, "$1 $2") | title | trim}}
publisher: {% if publicationTitle %}"{{publicationTitle}}"{% else %}"{{publisher}}"{% endif %}
{%- if notes.length > 0 -%}
{%- set longShortCutoff = 20 -%}
{%- set shortnotes = [] -%}
{%- set longnotes = [] -%}
{%- for note in notes -%}
{%- if note.note | wordcount <= longShortCutoff -%}
{%- set shortnotes = (shortnotes.push(note.note), shortnotes) -%} 
{%- else -%}
{%- set longnotes = (longnotes.push(note), longnotes) -%}
{%- endif -%}{%- endfor -%}{%- endif -%}
{%- for comment in shortnotes %}
{%- if comment and loop.first %}
comments:
{% endif -%}
- "{{comment|replace('"',"'")| replace("\n"," ")}}"{% endfor %}
tags:{% for t in tags %}
- {{t.tag | replace(r/\s+/g, "-")}}{% endfor %}{% if DOI %}
doi: https://doi.org/{{DOI}}{% endif %}{% if itemType == "book" %}
ISBN: {{ISBN}}{% endif %}
cssclasses: 
- literature-note{% if attachments.length > 0 %}{% for attachment in attachments %}{% if loop.first %}
attachments:{% endif %}
- {{attachment.path}}{% endfor %}{% endif %}
---
{% persist "notes" -%}
{%- if isFirstImport %}
{#  ==The following sections (Key takeaways and Processing) are not filled automatically. They are for for you to write into manually.== -#}
## Key takeaways

{#- The following is a cursor placeholder for the Templater plugin. After importing the note, you can jump to each of these with an assigned hotkey like ctrl+J  #}

- <% tp.file.cursor(1) %>

## Connections

- <% tp.file.cursor(4) %>

{% endif %}{% endpersist %}

> [!info]- Info 🔗 [**Zotero**]({{desktopURI}}){% if DOI %} | [**DOI**](https://doi.org/{{DOI}}){% endif %}{% for attachment in attachments | filterby("path", "endswith", ".pdf") %} | [**PDF-{{loop.index}}**](file:///{{attachment.path | replace(" ", "%20")}}){%- endfor %}
>
>{% if bibliography %}**Bibliography**: {{bibliography|replace("\n","" )}}{% endif %}
> 
> **Authors**:: {% for a in creators %} [[03 - Source notes/People/{{a.firstName}} {{a.lastName}}|{{a.firstName}} {{a.lastName}}]]{% if not loop.last %}, {% endif %}{% endfor %}
> 
> {% if tags %}**Tags**: {% for t in tags %}#{{t.tag | replace(r/\s+/g, "-")}}{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}
> 
> **Collections**:: {% for collection in collections %}[[{{collection.name}}]]{% if not loop.last %}, {% endif %}{% endfor -%}
{%- set readingSpeed = 220 %}
{%- set wordsPerPage = 360 %}
{%- if pages %}
    {%- set pageRegex = r/(\d+)\-(\d+)/ %}
    {%- set splitPages = pageRegex.test(pages) %}
    {%- if splitPages %}
        {%- set pageMatch = pageRegex.exec(pages) %}
        {%- set firstPage = pageMatch[1] %}
        {%- set pageCount = pageMatch[2] - pageMatch[1] %}
    {%- else %}
        {%- set pageCount = pages %}
    {%- endif %}
{%- elif numPages %}
    {%- set pageCount = numPages %}
{%- else %}
	{%- set pageCount = 0 %}
{% endif -%}
{%- if firstPage %}
>
> **First-page**:: {{firstPage}}
{%- endif -%}
{%- if pageCount > 0 -%}
    {%- set readingTime = ((pageCount* wordsPerPage)/readingSpeed)/60 %}
> 
> **Page-count**:: {{pageCount}}
> 
> **Reading-time**:: {% if readingTime < 1 %}{{(readingTime * 60) | round + " minutes"}}{% else %}{{readingTime | round(3) + " hours"}}{% endif %}{% endif %}

> [!abstract]-
> {% if abstractNote %}
> {{abstractNote|replace("\n","\n>")|striptags(true)|replace("Objectives", "**Objectives**")|replace("Background", "**Background**")|replace("Methodology", "**Methodology**")|replace("Results","**Results**")|replace("Conclusion","**Conclusion**")}}
> {% endif %}

> [!quote]- Citations
> 
> ```query
> content: "@{{citekey}}" -file:@{{citekey}}
> ```

{%- set headingRegex = r/^#+/ -%}
{%- set titleRegex = r/^#+.*/ -%}
{%- set lineRegex = r/^.*$/m %}
{%- if longnotes.length > 0 -%}
{%- for n in longnotes -%}
{%- if n and loop.first %}

> [!note]- Zotero notes ({{longnotes.length}})
> 
> Notes longer than {{longShortCutoff}} words.
{%- endif %}
>> [!example]- Note {{loop.index}} |{%- if headingRegex.test(n.note) == true %}[{{n.note | replace(n.note,titleRegex.exec(n.note))|replace(headingRegex,"")}}]({{n.uri}}){% else %} [{{lineRegex.exec(n.note | truncate(30))}}]({{n.uri}})
>> {% endif %}
>> {{n.note | replace("\n", "\n>> ")| replace(titleRegex, "")}}{% if n.tags.length > 0 %}
>>
>> Tags:{% for t in n.tags %} #{{t.tag}}{% if not loop.last %}, {% endif %}{% endfor %}{% endif -%}{%- if not loop.last %}
>{%- endif -%}
{%- endfor -%}{%- endif %}

___
## Reading notes

{% set colorValueMap = {
    "#ffd400": {
        "colorCategory": "Yellow",
        "heading": "💬 Evidence and arguments",
        "symbol": "&"
    },
	"#ff6666": {
        "colorCategory": "Red",
        "heading": "🚧 Digging and disclaimers",
        "symbol": "£"
    },
    "#5fb236": {
        "colorCategory": "Green",
        "heading": "🎯 Key takeaways",
        "symbol": "$"
    },
    "#2ea8e5": {
        "colorCategory": "Blue",
        "heading": "❓ Problem formulation",
        "symbol": "?"
    },
    "#aaaaaa": {
        "colorCategory": "Gray",
        "heading": "📌 Statistics and info",
        "symbol": "%"
    }
} -%}
{% set headingsMap = {
	"#a28ae5": {
        "colorCategory": "Purple",
        "heading": "🧩 Concepts and frameworks",
        "symbol": "~"
    },
    "#e56eee": {
        "colorCategory": "Magenta",
        "heading": "🗺️ Context and connections",
        "symbol": "€"
    },
    "#f19837": {
        "colorCategory": "Orange",
        "heading": "✅ Actionable takeaways",
        "symbol": "!"
    },
}}

{%- macro tagFormatter(annotation) -%}
    {% if annotation.tags -%}
        {%- for t in annotation.tags %} #{{ t.tag | replace(r/\s+/g, "-") }}{% if not loop.last %}, {% endif %}{%- endfor %}
    {%- endif %}
{%- endmacro -%}

{% persist "annotations" %}
{% set annotations = annotations | filterby("date", "dateafter", lastImportDate) -%}
{% if annotations.length > 0 %}
*Imported on [[{{importDate | format("YYYY-MM-DD")}}]] at {{importDate | format("HH:mm")}}*

{%- set grouped_annotations = annotations | groupby("color") -%}
{%- for color, colorValue in colorValueMap -%}
{%- if color in grouped_annotations -%} 
{%- set annotations = grouped_annotations[color] -%}
{%- for annotation in annotations -%}
{%- set citationLink = '[(p. ' ~ annotation.pageLabel ~ ')](' ~ annotation.desktopURI ~ ')' %}
{%- set tagString = tagFormatter(annotation) %}

{%- if annotation and loop.first %}

### {{colorValue.heading}} %% fold %%
{% endif -%}

{%- if annotation.imageRelativePath %}

> [!cite]+ Image {{citationLink}}
> ![[{{annotation.imageRelativePath}}]]{% if annotation.tags %}
> {{tagString}}{% endif %}{%- if (annotation.comment or []).indexOf("todo ") !== -1 %}
> - [ ] **{{annotation.comment | replace("todo ", "")}}**{%- elif annotation.comment %}
> **{{annotation.comment}}**{%- endif %}
{% elif (annotation.comment or []).indexOf("todo ") !== -1 %}
- [ ] **{{annotation.comment | replace("todo ", "")}}**:{% if not annotation.annotatedText %} {{citationLink}}{% else %}
	- {{colorValue.symbol}}  {{annotation.annotatedText | replace(r/\s+/g, " ")}} {{citationLink}}{{tagString}}{% endif -%}
{% elif annotation.comment %}
- **{{annotation.comment}}**:{% if not annotation.annotatedText %} {{citationLink}}{% else %}
	- {{colorValue.symbol}}  {{annotation.annotatedText | replace(r/\s+/g, " ") }} {{citationLink}}{{tagString}}{% endif -%}
{%- elif annotation.annotatedText %}
- {{colorValue.symbol}}  {{annotation.annotatedText | replace(r/\s+/g, " ") }} {{citationLink}}{{tagString}}
{%- endif -%}{%- endfor %}{%- endif -%}
{% endfor -%}
{% endif %}

{% endpersist %}

`BUTTON[update-litnote]`