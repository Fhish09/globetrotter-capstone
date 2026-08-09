/* Douala weather strip — Open-Meteo (no API key) */
(function () {
  function seasonTip() {
    var m = new Date().getMonth() + 1;
    if (m >= 3 && m <= 5) return '· Long rains approaching — pack a light poncho for walks';
    if (m >= 6 && m <= 10) return '· Rainy season: keep a museum slot for wet afternoons';
    if (m === 11 || m === 12 || m === 1 || m === 2) return '· Drier months: good for outdoor photos';
    return '· Coastal humidity is high — water and shade help';
  }

  function skyLabel(code) {
    if (code === 0) return 'Clear';
    if (code <= 3) return 'Partly cloudy';
    if (code <= 48) return 'Hazy / foggy';
    if (code <= 67) return 'Rain possible';
    if (code <= 77) return 'Showers';
    if (code <= 82) return 'Rain';
    return 'Storm risk';
  }

  async function load() {
    var live = document.getElementById('weatherLive');
    var season = document.getElementById('weatherSeason');
    if (season) season.textContent = seasonTip();
    if (!live) return;
    try {
      var url = 'https://api.open-meteo.com/v1/forecast?latitude=4.05&longitude=9.70&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=Africa%2FDouala';
      var res = await fetch(url);
      var data = await res.json();
      var c = data.current || {};
      var t = c.temperature_2m != null ? Math.round(c.temperature_2m) + '°C' : '—';
      var h = c.relative_humidity_2m != null ? c.relative_humidity_2m + '% humidity' : '';
      var w = c.wind_speed_10m != null ? Math.round(c.wind_speed_10m) + ' km/h' : '';
      var sky = skyLabel(c.weather_code);
      live.innerHTML = '<strong class="text-gt-text">' + t + '</strong> · ' + sky +
        (h ? ' · ' + h : '') + (w ? ' · ' + w : '');
    } catch (e) {
      live.textContent = 'Weather offline — see season tip';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
