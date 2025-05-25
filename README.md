# Kronoterm Cost Forecast for Home Assistant

Kronoterm Cost Forecast integration for Home Assistant provides a way to monitor and forecast costs associated with heating systems using Kronoterm (and possibly other) devices. This integration allows users to track energy consumption, costs and forecast usage.

## ⚙️ Requirements

- Home Assistant instance (at least version 2024.3)
- Kronoterm device integrated in Home Assistant (only consumption sensor reporting Watts is required)
- (Optional) ENTSOE API key (for energy prices in Ireland, Slovakia and Italy): <https://www.amsleser.no/blog/post/21-obtaining-api-token-from-entso-e>

## 🚀 Key Features

- Contains one line setup for HA instance with a Kronoterm device
- Support multiple energy price sources (most of European countries)
- Monitoring and forecasting energy price, consumption and costs
- Provides visualization of energy consumption and costs
- Compares costs between different time periods
- Supports multiple languages (English, Slovenian, German)

## 🖥️ Developers

Instructions for developers are available in [CODE.md](CODE.md) file.

## 📦 Installation

If you have an ENTSOE API key, you should set it as an environment variable `ENTSOE_API_KEY`.

<!--

### HACS Installation

If you are using HACS (Home Assistant Community Store), follow these steps to install the Kronoterm Cost Forecast integration:

TODO: Check?

1. **Add the repository:**
   - Go to HACS > Integrations > Add Repository
   - Enter the URL: `https://github.com/TPO-2024-2025/Kronoterm-Cost-Forecast.git`
   - Select the repository type as `Integration`.
2. **Install the integration:**
   - After adding the repository, search for "Kronoterm Cost Forecast" in HACS and install it.
   - Restart Home Assistant to apply the changes.
3. **Resources:**
   - Edit your `config` folder to include configurations for the custom component. While this is not strictly necessary, it is needed for more advanced visualizations.

   TODO: what?

4. **Restart Home Assistant.**

### Manual Installation

If you prefer to install the integration manually, follow these steps:

-->

1. **Download the integration:**
   - Using the command:

     ```bash
     git clone https://github.com/TPO-2024-2025/Kronoterm-Cost-Forecast
     ```

    or download the `.zip` file from GitHub and extract it.

   > [!TIP]
   > If you do not have your own Home Assistant instance, you can set it up with one line (assuming you have docker installed): `docker compose up` and you can skip to point [Configuration](#-configure-the-integration).

2. Install required dependencies by running the following command in `Kronoterm-Cost-Forecast` folder:

   ```bash
   pip install -r requirements.txt
   ```

3. **Copy the files**
   - Copy the contents of the `custom_components/kronoterm` folder to:

     ```console
     config/custom_components/kronoterm
     ```

4. **Set up configuration files (OPTIONAL):**
   - To enable advanced features, you can set up configuration files in your Home Assistant `config` folder. This step is optional but recommended for more advanced visualizations. The easiest way is to copy all content of `config` folder from the repository to your Home Assistant `config` folder, but you can also copy only the files you need:

   - Copy content of `config/www` folder to your Home Assistant `config/www` folder. Then load it into Home Assistant by adding the following line to your `configuration.yaml` file:

      ```yaml
      lovelace:
         mode: YAML
         resources:
            - url: /local/apexcharts-card.js?v=2.1.2
               type: module
            - url: /local/custom-apex-card.js
               type: module
      ```

   - Load `config/packages/kronofc_integration_loaded.yaml` into your Home Assistant configuration. You can do this by adding the following line to your `configuration.yaml` file:

     ```yaml
     packages: !include packages/kronofc_integration_loaded.yaml
     ```

     or even better, copy the content of `config/packages/kronofc_integration_loaded.yaml` to your `configuration.yaml` file directly.

   - Copy `config/lovelace/*.yaml` of visualization you want to your Home Assistant `config/lovelace` folder. Then include them in your `ui-lovelace.yaml` like this:

      ```yaml
      title: Home Dashboard
      views:
      - title: Main
         path: default_view
         cards:
            - !include lovelace/cost_forecast.yaml
            - !include lovelace/consumption_forecast.yaml
            - !include lovelace/sensors.yaml
            - !include lovelace/cost_comparison.yaml
      ```

5. **Restart Home Assistant.**

### 🔧 Configure the integration

- Go to Configuration > Integrations in Home Assistant.
- Click on "Add Integration" and search for "Kronoterm Cost Forecast".
- Select the integration and follow the prompts to configure it.
<!--- If you have an ENTSOE API key, you can enter it during the configuration process to enable energy price data.-->
- To connect consumer sensor, go to reconfiguration and select one of the available consumer sensors.
