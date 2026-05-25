<?php
/*
Plugin Name: ICO Atlas Contact Form
Description: Premium secure contact form with shortcode, glassmorphism design, spam protection, rate-limiting, and admin messages tracker.
Version: 1.0.0
Author: ICO Atlas Development
*/

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// 1. Table creation on plugin activation
register_activation_hook( __FILE__, 'iacf_activate_plugin' );
function iacf_activate_plugin() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'icoatlas_contact_messages';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE $table_name (
        id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
        name varchar(255) NOT NULL,
        email varchar(255) NOT NULL,
        company varchar(255) DEFAULT '' NOT NULL,
        ico varchar(32) DEFAULT '' NOT NULL,
        country varchar(8) DEFAULT '' NOT NULL,
        subject varchar(255) NOT NULL,
        message text NOT NULL,
        ip_hash varchar(64) NOT NULL,
        user_agent varchar(255) NOT NULL,
        status varchar(32) DEFAULT 'new' NOT NULL,
        created_at datetime NOT NULL,
        PRIMARY KEY  (id)
    ) $charset_collate;";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta( $sql );
}

// 2. Register REST API endpoint for form submission
add_action( 'rest_api_init', 'iacf_register_rest_routes' );
function iacf_register_rest_routes() {
    register_rest_route( 'icoatlas/v1', '/contact/submit', array(
        'methods'             => 'POST',
        'callback'            => 'iacf_submit_contact_form',
        'permission_callback' => '__return_true', // Public submission
    ) );
}

// 3. Rate limiting and honeypot validation on submission
function iacf_submit_contact_form( $request ) {
    // Honeypot check
    $params = $request->get_params();
    if ( ! empty( $params['website_url'] ) ) {
        // Silent block for bot spam
        return new WP_REST_Response( array(
            'success' => true,
            'message' => 'Vaša správa bola úspešne odoslaná.' // Fake success message to bots
        ), 200 );
    }

    // Rate Limiting Check (5 requests / 15 minutes)
    $ip = isset( $_SERVER['REMOTE_ADDR'] ) ? $_SERVER['REMOTE_ADDR'] : '127.0.0.1';
    $ip_hash = hash( 'sha256', $ip );
    $transient_key = 'iacf_rate_' . $ip_hash;
    $attempts = get_transient( $transient_key );

    if ( $attempts !== false && $attempts >= 5 ) {
        return new WP_Error(
            'rate_limit_exceeded',
            'Boli prekročené limity odosielania správ. Prosím, skúste to o 15 minút.',
            array( 'status' => 429 )
        );
    }

    // Inputs Validation
    $name = isset( $params['name'] ) ? trim( $params['name'] ) : '';
    $email = isset( $params['email'] ) ? trim( $params['email'] ) : '';
    $company = isset( $params['company'] ) ? trim( $params['company'] ) : '';
    $ico = isset( $params['ico'] ) ? trim( $params['ico'] ) : '';
    $country = isset( $params['country'] ) ? trim( $params['country'] ) : '';
    $subject = isset( $params['subject'] ) ? trim( $params['subject'] ) : '';
    $message = isset( $params['message'] ) ? trim( $params['message'] ) : '';
    $consent = isset( $params['consent'] ) ? (bool)$params['consent'] : false;

    if ( empty( $name ) || empty( $email ) || empty( $subject ) || empty( $message ) || ! $consent ) {
        return new WP_Error(
            'missing_required_fields',
            'Všetky povinné polia (meno, email, predmet, správa a súhlas) musia byť vyplnené.',
            array( 'status' => 400 )
        );
    }

    if ( ! is_email( $email ) ) {
        return new WP_Error(
            'invalid_email',
            'Prosím, zadajte platnú emailovú adresu.',
            array( 'status' => 400 )
        );
    }

    // Update transient for rate limiting
    if ( $attempts === false ) {
        set_transient( $transient_key, 1, 900 ); // 15 mins
    } else {
        set_transient( $transient_key, $attempts + 1, 900 );
    }

    // Sanitization
    $sanitized_name = sanitize_text_field( $name );
    $sanitized_email = sanitize_email( $email );
    $sanitized_company = sanitize_text_field( $company );
    $sanitized_ico = sanitize_text_field( $ico );
    $sanitized_country = sanitize_text_field( $country );
    $sanitized_subject = sanitize_text_field( $subject );
    $sanitized_message = sanitize_textarea_field( $message );
    $user_agent = isset( $_SERVER['HTTP_USER_AGENT'] ) ? substr( $_SERVER['HTTP_USER_AGENT'], 0, 255 ) : '';

    // Database logging
    global $wpdb;
    $table_name = $wpdb->prefix . 'icoatlas_contact_messages';
    $db_result = $wpdb->insert(
        $table_name,
        array(
            'name'       => $sanitized_name,
            'email'      => $sanitized_email,
            'company'    => $sanitized_company,
            'ico'        => $sanitized_ico,
            'country'    => $sanitized_country,
            'subject'    => $sanitized_subject,
            'message'    => $sanitized_message,
            'ip_hash'    => $ip_hash,
            'user_agent' => $user_agent,
            'created_at' => current_time( 'mysql' ),
            'status'     => 'new'
        ),
        array( '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s' )
    );

    // Email Sending
    $to = 'support@icoatlas.sk';
    $email_subject = '[ICO Atlas Contact] ' . $sanitized_subject;
    
    $email_body = "Meno: " . $sanitized_name . "\n";
    $email_body .= "Email: " . $sanitized_email . "\n";
    if ( ! empty( $sanitized_company ) ) {
        $email_body .= "Firma: " . $sanitized_company . "\n";
    }
    if ( ! empty( $sanitized_ico ) ) {
        $email_body .= "IČO: " . $sanitized_ico . "\n";
    }
    if ( ! empty( $sanitized_country ) ) {
        $email_body .= "Krajina: " . $sanitized_country . "\n";
    }
    $email_body .= "\nSpráva:\n" . $sanitized_message . "\n";

    $headers = array(
        'Reply-To: ' . $sanitized_name . ' <' . $sanitized_email . '>',
        'Content-Type: text/plain; charset=UTF-8'
    );

    $mail_sent = wp_mail( $to, $email_subject, $email_body, $headers );

    if ( ! $mail_sent ) {
        return new WP_REST_Response( array(
            'success' => false,
            'message' => 'Chyba pri odosielaní emailu. Správa bola však uložená do databázy.'
        ), 500 );
    }

    return new WP_REST_Response( array(
        'success' => true,
        'message' => 'Vaša správa bola úspešne odoslaná.'
    ), 200 );
}

// 4. Shortcode renderer [icoatlas_contact_form]
add_shortcode( 'icoatlas_contact_form', 'iacf_contact_form_renderer' );
function iacf_contact_form_renderer() {
    ob_start();
    ?>
    <div class="iacf-container">
        <style>
            .iacf-container {
                max-width: 680px;
                margin: 2rem auto;
                padding: 2.5rem;
                background: rgba(17, 24, 39, 0.8);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
                color: #f3f4f6;
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
            }
            .iacf-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
            }
            @media (max-width: 640px) {
                .iacf-grid {
                    grid-template-columns: 1fr;
                }
            }
            .iacf-group {
                display: flex;
                flex-direction: column;
                margin-bottom: 1.25rem;
            }
            .iacf-full {
                grid-column: span 2;
            }
            @media (max-width: 640px) {
                .iacf-full {
                    grid-column: span 1;
                }
            }
            .iacf-label {
                font-size: 0.875rem;
                font-weight: 500;
                margin-bottom: 0.5rem;
                color: #9ca3af;
            }
            .iacf-input, .iacf-textarea {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 0.75rem 1rem;
                color: #ffffff;
                font-size: 0.95rem;
                transition: border-color 0.25s, box-shadow 0.25s;
                outline: none;
                width: 100%;
                box-sizing: border-box;
            }
            .iacf-input:focus, .iacf-textarea:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
            }
            .iacf-textarea {
                resize: vertical;
                min-height: 120px;
            }
            .iacf-consent {
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
                margin-top: 0.5rem;
                margin-bottom: 1.5rem;
                cursor: pointer;
            }
            .iacf-checkbox {
                margin-top: 0.2rem;
                cursor: pointer;
            }
            .iacf-consent-text {
                font-size: 0.85rem;
                color: #9ca3af;
                line-height: 1.4;
            }
            .iacf-btn {
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: #ffffff;
                font-size: 1rem;
                font-weight: 600;
                padding: 0.875rem 2rem;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.2s, filter 0.2s;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
            }
            .iacf-btn:hover {
                filter: brightness(1.1);
                transform: translateY(-1px);
            }
            .iacf-btn:active {
                transform: translateY(0);
            }
            .iacf-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .iacf-honeypot {
                display: none !important;
            }
            .iacf-message {
                margin-top: 1.25rem;
                padding: 0.875rem 1.25rem;
                border-radius: 8px;
                font-size: 0.9rem;
                display: none;
            }
            .iacf-success {
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.3);
                color: #34d399;
            }
            .iacf-error {
                background: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.3);
                color: #f87171;
            }
        </style>

        <form id="iacf-form" novalidate>
            <div class="iacf-grid">
                <!-- Honeypot field -->
                <div class="iacf-honeypot">
                    <input type="text" name="website_url" id="iacf-website-url" tabindex="-1" autocomplete="off">
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-name">Meno a priezvisko *</label>
                    <input class="iacf-input" type="text" name="name" id="iacf-name" required>
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-email">E-mailová adresa *</label>
                    <input class="iacf-input" type="email" name="email" id="iacf-email" required>
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-company">Názov firmy</label>
                    <input class="iacf-input" type="text" name="company" id="iacf-company">
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-ico">IČO</label>
                    <input class="iacf-input" type="text" name="ico" id="iacf-ico">
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-country">Krajina</label>
                    <input class="iacf-input" type="text" name="country" id="iacf-country" placeholder="napr. SK, CZ">
                </div>

                <div class="iacf-group">
                    <label class="iacf-label" for="iacf-subject">Predmet *</label>
                    <input class="iacf-input" type="text" name="subject" id="iacf-subject" required>
                </div>

                <div class="iacf-group iacf-full">
                    <label class="iacf-label" for="iacf-message-body">Správa *</label>
                    <textarea class="iacf-textarea" name="message" id="iacf-message-body" required></textarea>
                </div>
            </div>

            <label class="iacf-consent" for="iacf-consent-chk">
                <input class="iacf-checkbox" type="checkbox" name="consent" id="iacf-consent-chk" required>
                <span class="iacf-consent-text">Súhlasím so spracovaním osobných údajov pre účely kontaktovania. *</span>
            </label>

            <button type="submit" class="iacf-btn" id="iacf-submit-btn">Odoslať správu</button>
            <div id="iacf-status-msg" class="iacf-message"></div>
        </form>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var form = document.getElementById('iacf-form');
                var submitBtn = document.getElementById('iacf-submit-btn');
                var statusMsg = document.getElementById('iacf-status-msg');

                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    statusMsg.style.display = 'none';
                    statusMsg.className = 'iacf-message';
                    
                    // Simple Frontend Validation
                    var name = document.getElementById('iacf-name').value.trim();
                    var email = document.getElementById('iacf-email').value.trim();
                    var subject = document.getElementById('iacf-subject').value.trim();
                    var message = document.getElementById('iacf-message-body').value.trim();
                    var consent = document.getElementById('iacf-consent-chk').checked;

                    if (!name || !email || !subject || !message || !consent) {
                        showError('Prosím, vyplňte všetky povinné polia a začiarknite súhlas so spracovaním údajov.');
                        return;
                    }

                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Odosiela sa...';

                    var formData = {
                        website_url: document.getElementById('iacf-website-url').value,
                        name: name,
                        email: email,
                        company: document.getElementById('iacf-company').value.trim(),
                        ico: document.getElementById('iacf-ico').value.trim(),
                        country: document.getElementById('iacf-country').value.trim(),
                        subject: subject,
                        message: message,
                        consent: consent ? 1 : 0
                    };

                    fetch('/wp-json/icoatlas/v1/contact/submit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    })
                    .then(function(res) {
                        return res.json().then(function(data) {
                            if (!res.ok) {
                                throw new Error(data.message || 'Došlo k chybe.');
                            }
                            return data;
                        });
                    })
                    .then(function(data) {
                        statusMsg.textContent = data.message;
                        statusMsg.classList.add('iacf-success');
                        statusMsg.style.display = 'block';
                        form.reset();
                    })
                    .catch(function(err) {
                        showError(err.message);
                    })
                    .finally(function() {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Odoslať správu';
                    });
                });

                function showError(msg) {
                    statusMsg.textContent = msg;
                    statusMsg.classList.add('iacf-error');
                    statusMsg.style.display = 'block';
                }
            });
        </script>
    </div>
    <?php
    return ob_get_clean();
}

// 5. Admin interface to track messages
add_action( 'admin_menu', 'iacf_add_admin_menu' );
function iacf_add_admin_menu() {
    global $menu;
    $menu_exists = false;
    foreach ( $menu as $item ) {
        if ( isset( $item[2] ) && $item[2] === 'icoatlas-menu' ) {
            $menu_exists = true;
            break;
        }
    }
    if ( ! $menu_exists ) {
        add_menu_page(
            'ICO Atlas',
            'ICO Atlas',
            'manage_options',
            'icoatlas-menu',
            'iacf_parent_menu_callback',
            'dashicons-shield',
            80
        );
    }

    add_submenu_page(
        'icoatlas-menu',
        'Contact Messages',
        'Contact Messages',
        'manage_options',
        'icoatlas-contact-messages',
        'iacf_admin_messages_page'
    );
}

function iacf_parent_menu_callback() {
    echo '<div class="wrap"><h1>ICO Atlas</h1><p>Vítejte v administraci ICO Atlas.</p></div>';
}

function iacf_admin_messages_page() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'icoatlas_contact_messages';

    // Handle Actions
    if ( isset( $_GET['action'] ) && isset( $_GET['id'] ) ) {
        check_admin_referer( 'iacf_msg_action' );
        $msg_id = intval( $_GET['id'] );
        $action = sanitize_text_field( $_GET['action'] );

        if ( in_array( $action, array( 'read', 'replied', 'delete' ) ) ) {
            if ( $action === 'delete' ) {
                $wpdb->delete( $table_name, array( 'id' => $msg_id ), array( '%d' ) );
                echo '<div class="updated"><p>Správa bola vymazaná.</p></div>';
            } else {
                $wpdb->update( $table_name, array( 'status' => $action ), array( 'id' => $msg_id ), array( '%s' ), array( '%d' ) );
                echo '<div class="updated"><p>Status správy bol upravený.</p></div>';
            }
        }
    }

    // Fetch Messages
    $messages = $wpdb->get_results( "SELECT * FROM $table_name ORDER BY created_at DESC" );
    ?>
    <div class="wrap">
        <h1 class="wp-heading-inline">ICO Atlas — Kontaktné správy</h1>
        <hr class="wp-header-end">

        <table class="wp-list-table widefat fixed striped table-view-list" style="margin-top: 1.5rem;">
            <thead>
                <tr>
                    <th style="width: 15%;">Dátum</th>
                    <th style="width: 15%;">Meno</th>
                    <th style="width: 15%;">Email</th>
                    <th style="width: 15%;">Firma / IČO</th>
                    <th style="width: 20%;">Predmet</th>
                    <th style="width: 10%;">Status</th>
                    <th style="width: 10%;">Akcie</th>
                </tr>
            </thead>
            <tbody>
                <?php if ( empty( $messages ) ) : ?>
                    <tr>
                        <td colspan="7">Žiadne správy neboli nájdené.</td>
                    </tr>
                <?php else : ?>
                    <?php foreach ( $messages as $msg ) : ?>
                        <tr>
                            <td><strong><?php echo esc_html( $msg->created_at ); ?></strong></td>
                            <td><?php echo esc_html( $msg->name ); ?></td>
                            <td><a href="mailto:<?php echo esc_attr( $msg->email ); ?>"><?php echo esc_html( $msg->email ); ?></a></td>
                            <td>
                                <?php 
                                    $company_info = array();
                                    if ( ! empty( $msg->company ) ) $company_info[] = $msg->company;
                                    if ( ! empty( $msg->ico ) ) $company_info[] = 'IČO: ' . $msg->ico;
                                    if ( ! empty( $msg->country ) ) $company_info[] = '(' . $msg->country . ')';
                                    echo esc_html( implode( ' ', $company_info ) );
                                ?>
                            </td>
                            <td><?php echo esc_html( $msg->subject ); ?></td>
                            <td>
                                <?php
                                    $status_label = 'Nová';
                                    $status_color = '#d63638';
                                    if ( $msg->status === 'read' ) {
                                        $status_label = 'Prečítaná';
                                        $status_color = '#1d2327';
                                    } elseif ( $msg->status === 'replied' ) {
                                        $status_label = 'Odpovedaná';
                                        $status_color = '#00a0d2';
                                    }
                                    echo '<span style="background:' . $status_color . '; color:#fff; padding:3px 8px; border-radius:3px; font-size:11px;">' . esc_html( $status_label ) . '</span>';
                                ?>
                            </td>
                            <td>
                                <button type="button" class="button button-small" onclick="document.getElementById('msg-detail-<?php echo esc_attr( $msg->id ); ?>').style.display = document.getElementById('msg-detail-<?php echo esc_attr( $msg->id ); ?>').style.display === 'none' ? 'table-row' : 'none';">
                                    Detail
                                </button>
                            </td>
                        </tr>
                        <tr id="msg-detail-<?php echo esc_attr( $msg->id ); ?>" style="display: none; background: #f6f7f7;">
                            <td colspan="7" style="padding: 1.5rem;">
                                <div style="max-width: 800px; background: #fff; padding: 1.5rem; border: 1px solid #c3c4c7; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                                    <h3 style="margin-top:0;">Detail správy</h3>
                                    <hr>
                                    <p><strong>Predmet:</strong> <?php echo esc_html( $msg->subject ); ?></p>
                                    <p><strong>Správa:</strong></p>
                                    <div style="background:#f0f0f1; padding: 1rem; border-radius:4px; white-space: pre-wrap; font-family: monospace; font-size: 13px; line-height: 1.5; color:#2c3338;"><?php echo esc_html( $msg->message ); ?></div>
                                    <hr>
                                    <p style="font-size:12px; color:#646970;">
                                        <strong>IP Hash:</strong> <?php echo esc_html( $msg->ip_hash ); ?> | 
                                        <strong>User Agent:</strong> <?php echo esc_html( $msg->user_agent ); ?>
                                    </p>
                                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                                        <?php if ( $msg->status !== 'read' ) : ?>
                                            <a href="<?php echo esc_url( wp_nonce_url( add_query_arg( array( 'action' => 'read', 'id' => $msg->id ) ), 'iacf_msg_action' ) ); ?>" class="button button-secondary">Označiť ako prečítanú</a>
                                        <?php endif; ?>
                                        <?php if ( $msg->status !== 'replied' ) : ?>
                                            <a href="<?php echo esc_url( wp_nonce_url( add_query_arg( array( 'action' => 'replied', 'id' => $msg->id ) ), 'iacf_msg_action' ) ); ?>" class="button button-secondary">Označiť ako odpovedanú</a>
                                        <?php endif; ?>
                                        <a href="<?php echo esc_url( wp_nonce_url( add_query_arg( array( 'action' => 'delete', 'id' => $msg->id ) ), 'iacf_msg_action' ) ); ?>" class="button button-link-delete" onclick="return confirm('Naozaj chcete vymazať túto správu?');" style="margin-left: auto; color:#d63638;">Vymazať správu</a>
                                    </div>
                                </div>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                <?php endif; ?>
            </tbody>
        </table>
    </div>
    <?php
}
