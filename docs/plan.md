čisté kódy + hard tipy, ako spraviť “Podobné články” rýchlo, pekne a bez lagov (WordPress, bez pluginov).
0) Speed cheat: ako to spraviť najrýchlejšie
Najrýchlejšie “hotové” riešenie = 1 funkcia + 1 shortcode + cache cez transient.
Výhoda: copy-paste do functions.php a používaš hneď.
1) Kompletný kód: Related Posts (kategórie/tagy) + fallback + cache
👉 Daj do functions.php (alebo vlastný plugin súbor):
<?php
/**
 * Related Posts (fast) - categories/tags + fallback + transient cache
 */

function h4_related_posts_get_ids($post_id, $limit = 3) {
    $post_id = (int) $post_id;
    $limit   = max(1, min(12, (int) $limit));

    // Cache key (per post + limit)
    $cache_key = "h4_rel_ids_{$post_id}_{$limit}";
    $cached = get_transient($cache_key);
    if (is_array($cached)) return $cached;

    $cats = wp_get_post_terms($post_id, 'category', ['fields' => 'ids']);
    $tags = wp_get_post_terms($post_id, 'post_tag', ['fields' => 'ids']);

    $base_args = [
        'post_type'           => 'post',
        'post_status'         => 'publish',
        'posts_per_page'      => $limit,
        'post__not_in'        => [$post_id],
        'ignore_sticky_posts' => true,
        'no_found_rows'       => true,
        'fields'              => 'ids',              // fastest
        'update_post_meta_cache' => false,
        'update_post_term_cache' => false,
    ];

    $ids = [];

    // 1) Try TAGS first (usually best relevance)
    if (!empty($tags)) {
        $q = new WP_Query(array_merge($base_args, [
            'tax_query' => [[
                'taxonomy' => 'post_tag',
                'field'    => 'term_id',
                'terms'    => $tags,
            ]],
        ]));
        $ids = $q->posts ?: [];
    }

    // 2) If not enough → add CATEGORIES
    if (count($ids) < $limit && !empty($cats)) {
        $need = $limit - count($ids);
        $q = new WP_Query(array_merge($base_args, [
            'posts_per_page' => $need,
            'post__not_in'   => array_merge([$post_id], $ids),
            'tax_query' => [[
                'taxonomy' => 'category',
                'field'    => 'term_id',
                'terms'    => $cats,
            ]],
        ]));
        $ids = array_merge($ids, $q->posts ?: []);
    }

    // 3) Fallback: latest posts in same post_type
    if (count($ids) < $limit) {
        $need = $limit - count($ids);
        $q = new WP_Query(array_merge($base_args, [
            'posts_per_page' => $need,
            'post__not_in'   => array_merge([$post_id], $ids),
        ]));
        $ids = array_merge($ids, $q->posts ?: []);
    }

    // Store transient (10 minutes – uprav podľa chuti)
    set_transient($cache_key, $ids, 10 * MINUTE_IN_SECONDS);
    return $ids;
}

function h4_related_posts_render($post_id = null, $limit = 3) {
    $post_id = $post_id ?: get_the_ID();
    if (!$post_id) return '';

    $ids = h4_related_posts_get_ids($post_id, $limit);
    if (empty($ids)) return '';

    ob_start(); ?>
    <section class="h4-related-posts" aria-label="Podobné články">
      <h3 style="margin:0 0 12px 0;">✦ Podobné články</h3>

      <div class="h4-related-grid">
        <?php foreach ($ids as $rid): 
          $title = get_the_title($rid);
          $url   = get_permalink($rid);
          $date  = get_the_date('j. F Y', $rid);
          $cats  = get_the_category($rid);
          $cat   = !empty($cats) ? $cats[0]->name : 'general';
          $ex    = get_the_excerpt($rid);
          ?>
          <article class="h4-related-card">
            <div class="h4-related-meta">
              <span class="h4-related-cat"><?php echo esc_html(strtolower($cat)); ?></span>
              <span class="h4-related-dot">•</span>
              <time datetime="<?php echo esc_attr(get_post_time('c', false, $rid)); ?>">
                <?php echo esc_html($date); ?>
              </time>
            </div>

            <h4 class="h4-related-title">
              <a href="<?php echo esc_url($url); ?>"><?php echo esc_html($title); ?></a>
            </h4>

            <?php if ($ex): ?>
              <p class="h4-related-excerpt"><?php echo esc_html(wp_trim_words($ex, 22)); ?></p>
            <?php endif; ?>

            <a class="h4-related-link" href="<?php echo esc_url($url); ?>">Čítať viac →</a>
          </article>
        <?php endforeach; ?>
      </div>
    </section>
    <?php
    return ob_get_clean();
}

/** Shortcode: [related_posts limit="3"] */
function h4_related_posts_shortcode($atts) {
    $atts = shortcode_atts(['limit' => 3], $atts);
    return h4_related_posts_render(get_the_ID(), (int)$atts['limit']);
}
add_shortcode('related_posts', 'h4_related_posts_shortcode');


/** Tiny CSS inline (alebo presuň do style.css) */
add_action('wp_head', function () { ?>
  <style>
    .h4-related-grid{display:grid;gap:16px;grid-template-columns:repeat(1,minmax(0,1fr));}
    @media(min-width:768px){.h4-related-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
    .h4-related-card{border:1px solid rgba(0,0,0,.08);border-radius:14px;padding:16px;background:#fff;}
    .h4-related-meta{font-size:13px;opacity:.8;margin-bottom:8px;display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
    .h4-related-title{margin:0 0 8px 0;font-size:16px;line-height:1.35;}
    .h4-related-title a{text-decoration:none;}
    .h4-related-title a:hover{text-decoration:underline;}
    .h4-related-excerpt{margin:0 0 10px 0;font-size:14px;opacity:.9;}
    .h4-related-link{font-weight:600;text-decoration:none;}
    .h4-related-link:hover{text-decoration:underline;}
    .h4-related-dot{opacity:.6;}
  </style>
<?php });
Použitie:
Do šablóny:
echo h4_related_posts_render(get_the_ID(), 3);
Alebo v editore (Gutenberg):
[related_posts limit="3"]
2) Tipy & triky, aby to bolo “raketa” (bez spomalenia webu)
✅ 1) fields => 'ids' + vypnúť cache term/meta
Už je v kóde. Toto je najväčší speed win.
✅ 2) Cache: transient (už je)
Pre “Podobné články” je úplne OK TTL 10–60 min.
✅ 3) Preprodukčné “ultra”: prepočítať pri uložení článku
Ak chceš byť extra, sprav:
save_post hook → vypočítať related IDs → uložiť do post meta h4_related_ids
endpoint potom už len číta meta (nula query navyše).
Keď chceš, dopíšem ti to tiež (je to +30 riadkov).
✅ 4) Fallback nech je vždy “niečo”
Aj keď článok nemá tagy/kategórie, user musí vidieť karty.
3) “Komplet funkčné vecičky” (bonusy)
Ak chceš, viem ti doplniť:
featured image + lazyload
reading time (“5 min čítania”)
“related by keywords” (z title/excerpt) bez AI
block editor (Gutenberg block) namiesto shortcode