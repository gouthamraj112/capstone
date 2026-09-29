/**
 * Time-based greeting utility for Smart Grid Operations Dashboard.
 * Dynamically computes greetings, icons, operational grid shift messages,
 * and live timestamp formatting based on the client's current local hour and language.
 */

export function getTimeGreeting(lang = 'en') {
  const now = new Date()
  const hour = now.getHours()

  // Determine period
  let period = 'morning'
  let icon = '🌅'

  if (hour >= 5 && hour < 12) {
    period = 'morning'
    icon = '🌅'
  } else if (hour >= 12 && hour < 17) {
    period = 'afternoon'
    icon = '☀️'
  } else if (hour >= 17 && hour < 21) {
    period = 'evening'
    icon = '🌆'
  } else {
    period = 'night'
    icon = '🌙'
  }

  const greetings = {
    en: {
      morning: 'Good morning',
      afternoon: 'Good afternoon',
      evening: 'Good evening',
      night: 'Good night',
      shift: {
        morning: 'Morning load ramping up · Monitoring morning baseload and peak demand.',
        afternoon: 'Mid-day operations active · Tracking high commercial load and solar balance.',
        evening: 'Evening peak transition · Monitoring residential surges and peak load.',
        night: 'Off-peak night hours · Low baseload demand and scheduled maintenance window.'
      }
    },
    es: {
      morning: '¡Buenos días!',
      afternoon: '¡Buenas tardes!',
      evening: '¡Buenas noches!',
      night: 'Buenas noches',
      shift: {
        morning: 'Aumento de carga matutina · Monitoreando demanda base y horas pico.',
        afternoon: 'Operaciones de mediodía · Seguimiento de alta demanda comercial.',
        evening: 'Transición pico nocturna · Vigilando sobrecargas residenciales.',
        night: 'Horas valle nocturnas · Baja demanda base y ventana de mantenimiento.'
      }
    },
    fr: {
      morning: 'Bonjour',
      afternoon: 'Bon après-midi',
      evening: 'Bonsoir',
      night: 'Bonne nuit',
      shift: {
        morning: 'Montée en charge matinale · Surveillance de la charge de base et des pointes.',
        afternoon: 'Opérations de mi-journée · Suivi de la forte demande commerciale.',
        evening: 'Pointe de début de soirée · Surveillance des hausses résidentielles.',
        night: 'Heures creuses de nuit · Faible demande de base et créneau de maintenance.'
      }
    },
    de: {
      morning: 'Guten Morgen',
      afternoon: 'Guten Tag',
      evening: 'Guten Abend',
      night: 'Gute Nacht',
      shift: {
        morning: 'Morgendlicher Lastanstieg · Überwachung von Grundlast und Spitzenbedarf.',
        afternoon: 'Mittagsbetrieb aktiv · Verfolgung hoher gewerblicher Lasten.',
        evening: 'Abendliche Spitzenlast · Überwachung des privaten Verbrauchs.',
        night: 'Schwachlastzeiten in der Nacht · Geringe Grundlast und Wartungsfenster.'
      }
    },
    zh: {
      morning: '早上好',
      afternoon: '下午好',
      evening: '晚上好',
      night: '夜深了，注意休息',
      shift: {
        morning: '早间负荷攀升期 · 实时监测晨间基荷与高峰需求。',
        afternoon: '午间负荷运行中 · 跟踪工商业用电高峰与供需平衡。',
        evening: '晚间用电高峰期 · 重点监控居民负荷与峰值波动。',
        night: '深夜低谷时段 · 基荷平稳运行与例行系统维护。'
      }
    },
    hi: {
      morning: 'सुप्रभात',
      afternoon: 'शुभ दोपहर',
      evening: 'शुभ संध्या',
      night: 'शुभ रात्रि',
      shift: {
        morning: 'सुबह की मांग में वृद्धि · मॉर्निंग बेसलोड और पीक डिमांड की निगरानी।',
        afternoon: 'दोपहर का संचालन सक्रिय · उच्च वाणिज्यिक मांग और संतुलन ट्रैकिंग।',
        evening: 'शाम की पीक अवधि · आवासीय खपत में वृद्धि की निगरानी।',
        night: 'ऑफ-पीक रात के घंटे · कम बेसलोड मांग और रखरखाव विंडो।'
      }
    }
  }

  const langPack = greetings[lang] || greetings.en
  const title = langPack[period] || langPack.morning
  const operationalSub = langPack.shift[period] || langPack.shift.morning

  // Formatted date & time
  const formattedTime = now.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })

  const formattedDate = now.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  })

  return {
    period,
    icon,
    text: title,
    subtext: operationalSub,
    formattedTime,
    formattedDate,
    fullStamp: `${formattedDate} · ${formattedTime}`
  }
}
