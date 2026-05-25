(ns dandy.macros)

(defn char-to-idx [c encoding-str]
  (let [idx (.indexOf encoding-str (int c))]
    (if (>= idx 0)
      idx
      (throw (IllegalArgumentException. (str "Unknown character: " c " (char code " (int c) ")"))))))

(defn parse-level [level-strings encoding-str]
  (let [flat-chars (apply str level-strings)]
    (mapv #(char-to-idx % encoding-str) flat-chars)))

(defmacro pre-parse-levels [raw-levels encoding-str]
  (let [parsed (mapv #(parse-level % encoding-str) raw-levels)]
    parsed))
