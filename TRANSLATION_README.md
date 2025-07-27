# Spanish Translation System

This Django project now supports Spanish translations alongside English. The internationalization (i18n) system has been fully implemented.

## What's Been Implemented

### 1. Settings Configuration

- Added `LANGUAGES` setting with English and Spanish
- Added `LOCALE_PATHS` pointing to the `locale/` directory
- Added `LocaleMiddleware` to handle language switching

### 2. URL Configuration

- Updated `timebank/urls.py` to use `i18n_patterns`
- Added language switcher URL at `/i18n/`
- URLs are now internationalized (e.g., `/es/services/`, `/en/services/`)

### 3. Translation Infrastructure

- Created `locale/es/LC_MESSAGES/` directory structure
- Generated initial translation files with `makemessages`
- Added sample Spanish translations for key strings

### 4. Updated Code Files

- **Views**: Added translation imports and wrapped user-facing messages
- **Forms**: Added translation for field labels and help text
- **Templates**: Added `{% load i18n %}` and `{% trans %}` tags
- **Navigation**: Added language switcher dropdown

### 5. Build Process Integration

- Updated `build.sh` to include translation compilation
- Added `makemessages` with proper ignore options to exclude `venv` and static directories
- Translations are now automatically compiled during deployment

## How to Use

### Language Switcher

Users can switch languages using the dropdown in the top navigation bar. The language switcher appears in both authenticated and non-authenticated views.

### Adding New Translations

1. **Mark strings for translation** in your code:

   ```python
   from django.utils.translation import gettext as _

   # In views
   messages.success(request, _("Your message has been sent successfully!"))

   # In forms
   name = forms.CharField(label=_("Name"))
   ```

2. **In templates**:

   ```html
   {% load i18n %}
   <h1>{% trans "Welcome to Saxapahaw Timebank" %}</h1>
   ```

3. **Generate translation files** (excluding venv and static directories):

   ```bash
   python manage.py makemessages -a --ignore=venv/* --ignore=staticfiles/* --ignore=static/*
   ```

   Or for a specific language:

   ```bash
   python manage.py makemessages -l es --ignore=venv/* --ignore=staticfiles/* --ignore=static/*
   ```

4. **Edit the translation file**:

   - Open `locale/es/LC_MESSAGES/django.po`
   - Add Spanish translations for each `msgstr ""` field

5. **Compile translations**:
   ```bash
   python manage.py compilemessages
   ```

### Translation Workflow

1. **Development**: Mark strings as you develop
2. **Extract**: Run `makemessages` with ignore options to update `.po` files
3. **Translate**: Edit the `.po` files with translations
4. **Compile**: Run `compilemessages` to create `.mo` files
5. **Test**: Switch languages in the UI to verify translations

### Production Deployment

The build process automatically handles translations:

1. **During build**: `makemessages` regenerates translation files (excluding venv)
2. **During build**: `compilemessages` compiles translations for production
3. **Runtime**: Django serves the compiled translations

## Current Translation Status

### ✅ Translated Areas

- Navigation menu items
- Home page content
- Form labels and placeholders
- Success/error messages in views
- Basic UI elements

### 🔄 Areas Needing Translation

- Service detail pages
- Request forms and pages
- User profile pages
- Admin interface (partially handled by Django)
- Email templates
- Dynamic content from database

## File Structure

```
locale/
├── es/
│   └── LC_MESSAGES/
│       ├── django.po    # Spanish translations
│       └── django.mo    # Compiled translations
└── en/
    └── LC_MESSAGES/
        ├── django.po    # English translations
        └── django.mo    # Compiled translations
```

## Best Practices

1. **Use translation functions consistently**:

   - `gettext as _` for views and Python code
   - `gettext_lazy as _` for model fields and forms
   - `{% trans %}` for template strings

2. **Context matters**: Some words have different meanings in different contexts. Use `pgettext` for context-specific translations.

3. **Pluralization**: Use `ngettext` for strings that change based on number.

4. **Keep translations up to date**: Run `makemessages` regularly during development.

5. **Exclude unnecessary directories**: Always use `--ignore` options to exclude `venv`, `staticfiles`, and `static` directories.

## Testing Translations

1. Start the development server:

   ```bash
   python manage.py runserver
   ```

2. Visit the site and use the language switcher to test Spanish translations

3. Check that all user-facing text is properly translated

## Adding More Languages

To add another language (e.g., French):

1. Add to `LANGUAGES` in settings:

   ```python
   LANGUAGES = [
       ('en', 'English'),
       ('es', 'Spanish'),
       ('fr', 'French'),
   ]
   ```

2. Generate translation files:

   ```bash
   python manage.py makemessages -l fr --ignore=venv/* --ignore=staticfiles/* --ignore=static/*
   ```

3. Translate the `.po` file and compile:
   ```bash
   python manage.py compilemessages
   ```

## Troubleshooting

- **Translations not showing**: Make sure you've run `compilemessages`
- **Missing translations**: Check that strings are properly marked with `_()` or `{% trans %}`
- **Language switcher not working**: Verify `LocaleMiddleware` is in `MIDDLEWARE`
- **URLs not working**: Check that `i18n_patterns` is properly configured
- **Translation files too large**: Use `--ignore` options to exclude venv and static directories
- **Production translations not working**: Ensure `compilemessages` is in your build script

## Build Script Integration

The `build.sh` script now includes:

```bash
# Generate translation files (excluding venv and static directories)
python manage.py makemessages -a --ignore=venv/* --ignore=staticfiles/* --ignore=static/*

# Compile translations for production
python manage.py compilemessages
```

This ensures that:

- Translation files are clean (no venv strings)
- Translations are compiled during deployment
- Production has the latest translations

## Next Steps

1. **Complete translations**: Add Spanish translations for all remaining user-facing text
2. **Email templates**: Translate email templates and notifications
3. **Dynamic content**: Consider translating database content (categories, etc.)
4. **Testing**: Create comprehensive tests for translation functionality
5. **Documentation**: Translate user documentation and help text
6. **Quality assurance**: Review and refine existing translations for accuracy and naturalness
