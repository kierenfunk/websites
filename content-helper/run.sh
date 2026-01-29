#!/bin/sh

#########
# SETUP #
#########

CUT_OFF_DATE="$1"
SITE_NAME="$2"
SITE_ROOT_URL="$3"
mkdir -p src/assets src/blog
rm -f /tmp/99-content-*.html /tmp/posts.html

#######################
# GET THE INDEX PAGES #
#######################
seq "$(date -d "$CUT_OFF_DATE" +%Y)" $(date +%Y) | xargs -I {} wget "https://finance-matters.info/{}/" -O "/tmp/99-content-{}.html"

######################
# GET THE BLOG PAGES #
######################

cat /tmp/99-content-*.html | \
grep -oP "<a href=\"\Khttps://finance-matters.info/[\d]{4}/[\d]{2}/[\d]{2}/[^/^\"]+" | sort -r | uniq | \
awk \
	-v day="$(date -d "$CUT_OFF_DATE" +%d)" \
	-v month="$(date -d "$CUT_OFF_DATE" +%m)" \
	-v year="$(date -d "$CUT_OFF_DATE" +%Y)" \
	-F '/' \
	'$6 >= day && $5 >= month && $4 >= year {print $4 "-" $5 "-" $6,$0}' \
	> /tmp/meta.txt

while read -r article_date og_url; do
	wget $og_url -nc --adjust-extension -P "content"
	file="content/$(basename $og_url).html"
	dest="src/blog/$(basename $og_url).html"
	href="/blog/$(basename $og_url)"
	title=$(cat $file | grep -oP -m 1 "<meta property=\"og:title\" content=\"\K[^\"]+")
	description=$(cat $file | grep -oP -m 1 "<meta property=\"og:description\" content=\"\K[^\"]+")
	published_time=$(cat $file | grep -oP -m 1 "<meta property=\"og:article:published_time\" content=\"\K[^\"]+")
	modified_time=$(cat $file | grep -oP -m 1 "<meta property=\"og:article:modified_time\" content=\"\K[^\"]+")
	og_img_url=$(cat $file | grep -oP -m 1 "<meta property=\"og:image\" content=\"\K[^\"]+")
	img_url="/assets/$(basename $og_img_url)"
	img_url_ne=${img_url%.*}
	img_width=$(cat $file | grep -oP -m 1 "<meta property=\"og:image:width\" content=\"\K[^\"]+")
	img_height=$(cat $file | grep -oP -m 1 "<meta property=\"og:image:height\" content=\"\K[^\"]+")
	img_type=$(cat $file | grep -oP -m 1 "<meta property=\"og:image:type\" content=\"\K[^\"]+")
	human_article_date=$(date -d "$article_date" +'%B %-d, %Y')

	# download and convert images
	if [ ! -e "src$img_url" ]; then
		wget $og_img_url -P "/tmp/assets"
		cp "/tmp$img_url" "src$img_url"
	fi
	img_widths=("1100" "1024" "768" "300")
	for width in "${img_widths[@]}"; do
		if [ ! -e "src$img_url_ne-${width}w.avif" ]; then
			magick "/tmp$img_url" -resize "${width}x" "src$img_url_ne-${width}w.avif"
		fi
	done

	article_body=$(cat $file | sed -nE '/<article class="small single">/,/<p><strong>Disclaimer:/p' | sed -E -e 's/.*<article class="small single">//' -e 's/<\/span>//g' -e 's/<span[^>]*>//g')

	cat > $dest << EOF
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta content="width=device-width, initial-scale=1" name="viewport"><link href="/favicon/apple-touch-icon.png" rel="apple-touch-icon" sizes="180x180"><link href="/favicon/favicon-32x32.png" rel="icon" sizes="32x32" type="image/png"><link href="/favicon/favicon-16x16.png" rel="icon" sizes="16x16" type="image/png"><link href="/favicon/site.webmanifest" rel="manifest"><title>$title | $SITE_NAME</title>
<link href="$SITE_ROOT_URL$href" rel="canonical">
<meta content="$title" property="og:title">
<meta content="$description" property="og:description">
<meta content="article" property="og:type">
<meta property="og:article:published_time" content="$published_time">
<meta property="og:article:modified_time" content="$modified_time">
<meta property="og:image" content="$SITE_ROOT_URL$img_url"/>
<meta property="og:image:width" content="$img_width">
<meta property="og:image:height" content="$img_height">
<meta property="og:image:type" content="$img_type">
<meta content="$SITE_ROOT_URL$href" property="og:url">
<meta content="$SITE_NAME" property="og:site_name">
<link href="/main.css" rel="stylesheet">
</head>
<body>
<header data-ssg="header"></header>
<main class="bg-gray-100">
<article id="article">
<h1>$title</h1>
<p>🗓️ $human_article_date</p>
<picture>
<source media="(min-width:1100px)" srcset="$img_url_ne-1100w.avif">
<source media="(min-width:1024px)" srcset="$img_url_ne-1024w.avif">
<source media="(min-width:768px)" srcset="$img_url_ne-768w.avif">
<source srcset="$img_url_ne-300w.avif">
<img src="$img_url" alt="$title" width="$img_width" height="$img_height" fetchpriority="high" decode="async">
</picture>$article_body</article></main><section data-ssg="cta"></section><footer data-ssg="footer"></footer><script src="/borsuk.js" defer></script><script src="/main.js" defer></script></body></html>
EOF

	cat >> /tmp/posts.html << EOF  
<a class="post" href="$href" itemscope itemtype="https://schema.org/Article"><picture><source srcset="$img_url_ne-768w.avif"><img loading="lazy" src="$img_url" alt="$title" itemprop="image"></picture><h4 itemprop="headline">$title</h4><p itemprop="description">$description</p><p itemprop="datePublished" content="$article_date">🗓️ $human_article_date</p></a>
EOF
done < /tmp/meta.txt

# build new index page
tr '\n' ' ' < src/index.html | grep -oP '.*<div[^>]*data-ssg="posts"[^>]*>' > /tmp/new-index.html
cat /tmp/posts.html | head -n 3 >> /tmp/new-index.html
tr '\n' ' ' < src/index.html | grep -oP '.*<a [^>]+itemtype="https://schema.org/Article">.*?</a>\K.*' >> /tmp/new-index.html
mv /tmp/new-index.html src/index.html

# build new blog page
tr '\n' ' ' < src/blog.html | grep -oP '.*<div[^>]*data-ssg="posts"[^>]*>' > /tmp/new-blog.html
cat /tmp/posts.html >> /tmp/new-blog.html
tr '\n' ' ' < src/blog.html | grep -oP '.*<a [^>]+itemtype="https://schema.org/Article">.*?</a>\K.*' >> /tmp/new-blog.html
mv /tmp/new-blog.html src/blog.html
