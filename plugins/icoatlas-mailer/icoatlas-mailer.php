<?php
/*
Plugin Name: ICO Atlas Mailer
Description: Custom secure SMTP mailer configuration for support@icoatlas.sk using Websupport.
Version: 1.0.0
Author: ICO Atlas Development
*/

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

add_action( 'phpmailer_init', 'icoatlas_mailer_smtp_init' );
function icoatlas_mailer_smtp_init( $phpmailer ) {
    $smtp_password = getenv( 'SMTP_PASSWORD' );
    
    // Check if the environment variable is set
    if ( empty( $smtp_password ) ) {
        return;
    }

    $phpmailer->isSMTP();
    $phpmailer->Host       = 'smtp.m1.websupport.sk';
    $phpmailer->SMTPAuth   = true;
    $phpmailer->Port       = 465;
    $phpmailer->Username   = 'support@icoatlas.sk';
    $phpmailer->Password   = $smtp_password;
    $phpmailer->SMTPSecure = 'ssl';
    $phpmailer->From       = 'support@icoatlas.sk';
    $phpmailer->FromName   = 'ICO Atlas Support';
}

// Ensure default from name and email are set correctly
add_filter( 'wp_mail_from', 'icoatlas_mailer_default_from' );
function icoatlas_mailer_default_from( $original_email_address ) {
    return 'support@icoatlas.sk';
}

add_filter( 'wp_mail_from_name', 'icoatlas_mailer_default_from_name' );
function icoatlas_mailer_default_from_name( $original_email_from ) {
    return 'ICO Atlas Support';
}
