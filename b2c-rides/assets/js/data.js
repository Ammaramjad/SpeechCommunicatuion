window.RIDEDATA = {
  copy: {
    en: {
      hubTitle: "RideLook B2C — taxi & car booking only",
      hubSub: "Klook-style look, but only the transport category. Two customer demos.",
      demoA: "Demo A · Transfer marketplace",
      demoB: "Demo B · Instant city taxi",
      demoABody: "Airport pickup, airport drop, hourly private car, intercity. Search → cars → checkout.",
      demoBBody: "Book a taxi now on a live map. Choose Mini / Sedan / SUV / Luxury, match a driver, track the ride.",
      openA: "Open marketplace demo",
      openB: "Open taxi demo",
      hero: "Private cars, airport transfers & taxis",
      heroSub: "Same marketplace feel as Klook — focused only on rides.",
      search: "Search cars",
      popular: "Popular airport transfers",
      why: "Why travellers book RideLook",
      results: "Available cars",
      book: "Book now",
      checkout: "Checkout",
      pay: "Pay & confirm",
      done: "Booking confirmed",
      where: "Where to?",
      confirmRide: "Confirm ride",
    },
    hi: {
      hubTitle: "RideLook B2C — सिर्फ टैक्सी और कार बुकिंग",
      hubSub: "Klook जैसा लुक, लेकिन सिर्फ ट्रांसपोर्ट कैटेगरी। कस्टमर के लिए दो डेमो।",
      demoA: "डेमो A · ट्रांसफर मार्केटप्लेस",
      demoB: "डेमो B · इंस्टेंट सिटी टैक्सी",
      demoABody: "एयरपोर्ट पिकअप, ड्रॉप, hourly प्राइवेट कार, इंटरसिटी। सर्च → कारें → चेकआउट।",
      demoBBody: "अभी टैक्सी बुक करें। Mini / Sedan / SUV / Luxury चुनें, ड्राइवर मैच, लाइव ट्रैकिंग।",
      openA: "मार्केटप्लेस डेमो खोलें",
      openB: "टैक्सी डेमो खोलें",
      hero: "प्राइवेट कार, एयरपोर्ट ट्रांसफर और टैक्सी",
      heroSub: "Klook जैसा मार्केटप्लेस फील — फोकस सिर्फ राइड्स पर।",
      search: "कारें खोजें",
      popular: "पॉपुलर एयरपोर्ट ट्रांसफर",
      why: "यात्री RideLook क्यों बुक करते हैं",
      results: "उपलब्ध कारें",
      book: "अभी बुक करें",
      checkout: "चेकआउट",
      pay: "पेमेंट करके कन्फर्म करें",
      done: "बुकिंग कन्फर्म",
      where: "कहाँ जाना है?",
      confirmRide: "राइड कन्फर्म करें",
    },
  },
  routes: [
    { id: "del-cp", from: "DEL — Indira Gandhi Airport", to: "Connaught Place, Delhi", fromPrice: 1490, img: "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=800&q=60", mins: 45 },
    { id: "bom-bandra", from: "BOM — Mumbai Airport", to: "Bandra West", fromPrice: 890, img: "https://images.unsplash.com/photo-1529253355930-ddbe923a94d2?auto=format&fit=crop&w=800&q=60", mins: 35 },
    { id: "blr-kora", from: "BLR — Kempegowda Airport", to: "Koramangala", fromPrice: 1290, img: "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=800&q=60", mins: 55 },
    { id: "goi-cal", from: "GOI — Goa Airport", to: "Calangute Beach", fromPrice: 1190, img: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=800&q=60", mins: 50 },
  ],
  places: [
    "DEL — Indira Gandhi Airport",
    "BOM — Mumbai Airport",
    "BLR — Kempegowda Airport",
    "GOI — Goa Airport",
    "HYD — Rajiv Gandhi Airport",
    "Connaught Place, Delhi",
    "Bandra West, Mumbai",
    "Koramangala, Bengaluru",
    "Calangute Beach, Goa",
    "Hitech City, Hyderabad",
    "Jaipur City Palace",
  ],
  cars: [
    { id: "swift", name: "Hatchback · Maruti Swift", type: "Hatchback", seats: 3, bags: 2, rating: 4.7, reviews: 1284, price: 890, old: 1100, img: "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=900&q=60", amenities: ["AC", "English-speaking driver"], meet: false },
    { id: "dzire", name: "Sedan · Dzire / Etios", type: "Sedan", seats: 3, bags: 3, rating: 4.8, reviews: 3421, price: 1290, old: 1590, img: "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=900&q=60", amenities: ["Meet & greet", "AC", "Flight tracking"], meet: true },
    { id: "innova", name: "MPV · Innova Crysta", type: "SUV", seats: 6, bags: 5, rating: 4.9, reviews: 2109, price: 2190, old: 2690, img: "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=900&q=60", amenities: ["Meet & greet", "Child seat", "Water"], meet: true },
    { id: "fortuner", name: "SUV · Fortuner / XUV700", type: "SUV", seats: 5, bags: 4, rating: 4.8, reviews: 876, price: 2890, old: 3400, img: "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=60", amenities: ["Premium", "Meet & greet"], meet: true },
    { id: "eclass", name: "Luxury · Mercedes E-Class", type: "Luxury", seats: 3, bags: 3, rating: 4.9, reviews: 412, price: 5490, old: 6200, img: "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=900&q=60", amenities: ["Chauffeur", "Wi-Fi", "Water"], meet: true },
    { id: "tempo", name: "Tempo Traveller 12 seater", type: "Van", seats: 12, bags: 12, rating: 4.6, reviews: 301, price: 4990, old: 5600, img: "https://images.unsplash.com/photo-1464219789935-c2d9d9aba894?auto=format&fit=crop&w=900&q=60", amenities: ["Group", "AC"], meet: false },
  ],
  taxiClasses: [
    { id: "mini", name: "Mini", eta: "3 min", price: 149, desc: "Compact AC hatchback", img: "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=200&q=60" },
    { id: "sedan", name: "Sedan", eta: "4 min", price: 219, desc: "Comfort sedan, 3 bags", img: "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=200&q=60" },
    { id: "suv", name: "SUV", eta: "6 min", price: 349, desc: "Family SUV, extra space", img: "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=200&q=60" },
    { id: "lux", name: "Luxury", eta: "9 min", price: 799, desc: "Chauffeur luxury sedan", img: "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=200&q=60" },
  ],
};

window.RideLook = {
  lang: localStorage.getItem("rl-lang") || "en",
  t(key) {
    return RIDEDATA.copy[this.lang][key] || RIDEDATA.copy.en[key] || key;
  },
  toggleLang() {
    this.lang = this.lang === "en" ? "hi" : "en";
    localStorage.setItem("rl-lang", this.lang);
    location.reload();
  },
  inr(n) {
    return "₹" + n.toLocaleString("en-IN");
  },
};
