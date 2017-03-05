'use strict';
var gulp = require('gulp');
var plug = require('gulp-load-plugins')();
var del = require('del');

var config = require('./config.json');

gulp.task('dist', ['clean', 'copy', 'fonts', 'vendor:prod', 'js:prod', 'css:prod', 'templates']);

// Clean static/admin folder except /images
gulp.task('clean', function (cb) {
    del.sync([config.bases.dist + '/**/*.*',
              '!' + config.bases.dist + '/images/*.*'
              ], {force: true});
    cb();
});

// Copy src/assets to static/admin/assets
gulp.task('copy', function () {
    gulp.src(config.path.copy, {read: true})
        .pipe(gulp.dest(config.bases.dist));
});

// Watch for changes in src/assets/ and call copy task if there were changes
gulp.task('copy:watch', function () {
    gulp.watch(config.path.copy, ['copy']);
});

// Copy vendor/font-awesome/fonts and  vendor/bootstrap/fonts/ in
// static/admin/fonts/
gulp.task('fonts', function () {
    gulp.src(config.path.fonts, {read: true})
        .pipe(gulp.dest(config.bases.dist+'fonts/'));
});

// Inject app.vendor.js and app.vendor.css generated in 'vendor:js:prod'
// and 'vendor:css:prod' tasks in /maplocate/templates/index.jinja2
gulp.task('vendor:prod', ['vendor:js:prod', 'vendor:css:prod'], function() {
    gulp.src('../maplocate/templates/index.jinja2')
        .pipe(plug.inject(gulp.src([
            config.bases.dist + 'js/app.vendor.js',
            config.bases.dist + 'css/app.vendor.css'
        ]), {
            name: 'vendor',
            addPrefix: 'static',
            ignorePath: '../static'
        }))
        .pipe(gulp.dest('../maplocate/templates/'));
});

// Concatenate js scripts from "libs" in config.json as app.vendor.js,
// uglify it and put in /static/admin/js/app.vendor.js
gulp.task('vendor:js:prod', function() {
    return gulp.src(config.path.libs)
        .pipe(plug.concat('app.vendor.js'))
        .pipe(plug.uglify())
        .pipe(gulp.dest(config.bases.dist + '/js'));
});

// Concatenate css from "css_libs" in config.json (bootstrap, toastr, fonts
// etc.) as app.vendor.css and put it in /static/admin/css/app.vendor.css'
gulp.task('vendor:css:prod', function() {
    return gulp.src(config.path.css_libs)
        .pipe(plug.concat('app.vendor.css'))
        .pipe(gulp.dest(config.bases.dist + '/css'));
});

// Concatenate all scripts from src/app/... and src/common/... in app.js,
// uglify it and put in /static/admin/js/app.js
gulp.task('js:prod', function () {
    gulp.src(config.path.scripts)
        .pipe(plug.plumber())
        .pipe(plug.concat('app.js'))
        .pipe(plug.uglify())
        .pipe(gulp.dest(config.bases.dist + '/js'));
});

// Copy src/scss/app.scss to /admin/static/css/ folder
gulp.task('css:prod', function () {
    gulp.src(config.path.sass.src)
        .pipe(plug.plumber())
        .pipe(plug.sass(config.path.sass.conf))
        .pipe(gulp.dest(config.bases.dist + '/css'));
});

// Convert all tpl.html files under src/app/ in one app.tpls.js and put in
// /admin/static/js/app.tpls.js - it used in index.jinja2 template
gulp.task('templates', function() {
    gulp.src(config.path.html)
        .pipe(plug.angularTemplatecache('app.tpls.js', {
            module: 'app.tpls',
            standalone: true
        }))
        .pipe(gulp.dest(config.bases.dist + '/js'));
});

// Watch if any changes happen in html templates inside src/app/ folder and
// execute templates task if there were changes
gulp.task('templates:watch', function () {
    gulp.watch(config.path.html, ['templates']);
});
