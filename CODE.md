# Code Documentation

Structure of repository is as follows:

- `custom_component/kronoterm` Home Assistant custom component written in Python
- `tests` Unit tests for the custom component
- `config` Yaml configuration files for Home Assistant
- `custom_cards` npm package for our custom cards for Home Assistant Lovelace UI that enables advanced visualizations of the data
- `docker-compose.yml` Docker Compose file for setting up Home Assistant instance

[![Organization of components](https://img.plantuml.biz/plantuml/svg/ZLPDZzem4BtdLrZqK1KfKYaVos65DXj1bsf58x7jfQqgapXWuTZ8TfRzqFxtZWqbYPCiv135Cy_FxysO4JTAOwdpZ7bgI_aEIvoX5OwtQobodiI22Ods6wf9AP-G5ETCFv0d7J2wvXdX6iNm8hA42gGK-z0Ih1WmbbAno7Q2crsl7geTzu6Cqs6Qr3FNrofVgMUbIJQP75K1ICY4oEFMuUnsF0szjz9XrEXASKpE7TR8up6IQgG5adIzqIYXaiIQ2kvvXOdEdSW82fIYK4okEwWgzDK3zbRqRzxjJXzDuZPNtMu7OONk0g0uxPXC789xyKYOCVHZRk4CrlKDDkh_sj0a8VoF3wIUyLFmnBdI8ljR11fa5yMRSYBNpq4q1zWfwaexWLID3Dcd15qyBBzF7TakQ04zYOHWPs27OyCDt6Hr1lfrkfYVOsDagwMu_rR3lHctHI4--VwaPBcf596aCLaIheGyRIt5K8N147o4tf-QPkwUty1KQSoH2Ux1yhFJ6sHkakz30ZuX2uARsGhPeL2wY5VKv3lVIJUAwBM9w1aHFIlY0felDHe8cRrmZ-rtZQPiWgiy8xB5I2Bst6y0DUhejzdf6ndzevsBg0PrIuEIfG5gf2fiHP8aDDRk2Hrafq1aef7bAu388JH7HCuu0KHArsZ6nDuI7TPcMQkS7OA-WwWfMGxRQZOqFeV_Q_OknwXUh56fM2FaS5H6sq_wacD6Nx0PrSspoBqjEmET2HZlMEc62L7zYLmC36659LM2Er3GMp8TOfceW_4hn_XXZaFnhZp8cGfKtPLzXtQaMx9pfYqos94dWtvNsx4XupPTOmzojgKLJi-x8Jo1VnR_0000)](https://editor.plantuml.com/uml/ZLPDZzem4BtdLrZqK1KfKYaVos65DXj1bsf58x7jfQqgapXWuTZ8TfRzqFxtZWqbYPCiv135Cy_FxysO4JTAOwdpZ7bgI_aEIvoX5OwtQobodiI22Ods6wf9AP-G5ETCFv0d7J2wvXdX6iNm8hA42gGK-z0Ih1WmbbAno7Q2crsl7geTzu6Cqs6Qr3FNrofVgMUbIJQP75K1ICY4oEFMuUnsF0szjz9XrEXASKpE7TR8up6IQgG5adIzqIYXaiIQ2kvvXOdEdSW82fIYK4okEwWgzDK3zbRqRzxjJXzDuZPNtMu7OONk0g0uxPXC789xyKYOCVHZRk4CrlKDDkh_sj0a8VoF3wIUyLFmnBdI8ljR11fa5yMRSYBNpq4q1zWfwaexWLID3Dcd15qyBBzF7TakQ04zYOHWPs27OyCDt6Hr1lfrkfYVOsDagwMu_rR3lHctHI4--VwaPBcf596aCLaIheGyRIt5K8N147o4tf-QPkwUty1KQSoH2Ux1yhFJ6sHkakz30ZuX2uARsGhPeL2wY5VKv3lVIJUAwBM9w1aHFIlY0felDHe8cRrmZ-rtZQPiWgiy8xB5I2Bst6y0DUhejzdf6ndzevsBg0PrIuEIfG5gf2fiHP8aDDRk2Hrafq1aef7bAu388JH7HCuu0KHArsZ6nDuI7TPcMQkS7OA-WwWfMGxRQZOqFeV_Q_OknwXUh56fM2FaS5H6sq_wacD6Nx0PrSspoBqjEmET2HZlMEc62L7zYLmC36659LM2Er3GMp8TOfceW_4hn_XXZaFnhZp8cGfKtPLzXtQaMx9pfYqos94dWtvNsx4XupPTOmzojgKLJi-x8Jo1VnR_0000)

## Development of custom component

This custom component is managed as pyproject where the code is written in Python and uses `uv` for dependency management and virtual environment setup:

1. Install `uv` using instructions provided in <https://docs.astral.sh/uv/getting-started/installation/#installation-methods>
2. Run `uv sync` to install deps and setup venv
3. Make sure vscode uses uv's venv
4. Programme and run various commands:
   - `uv run ruff check` to check fmt and style
   - `uv run mypy .` to check typing
   - `uv run pytest` to run tests
   - `source .venv/bin/activate` or `.venv\Scripts\activate` to enter `venv`

Changes can be tested by creating fresh HA instance, which can be quickly done using `docker compose up` in the root of the project. This will create a new Home Assistant instance with the custom component pre-installed, but not yet configured.

Do not forget to restart Home Assistant after making changes to the code or configuration files.

## Development of custom cards

Custom cards are developed as an npm package. To develop them, you must have node installed, follow these steps:

1. Install the required dependencies:

   ```bash
   cd custom_cards
   npm install
   ```

2. Start the development server:

   ```bash
   npm run dev
   ```

3. Make changes to the source code in the `src` directory. The development server will automatically reload the changes.

4. Build the package for production:

   ```bash
   npm run build
   ```

   copy the contents of the `dist` folder to `config/www` folder.
