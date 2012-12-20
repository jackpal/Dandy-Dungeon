(ns dandy-clj.core)

(import '(javax.swing ImageIcon JLabel JPanel JFrame JTextField SwingUtilities)
        '(javax.swing.event DocumentListener)
        '(java.awt GridBagLayout GridBagConstraints Insets))

(def levelWidth 60)
(def levelHeight 30)
(def tileWidth 16)
(def tileHeight 16)
(def windowTileWidth 20)
(def windowTileHeight 10)

(def kSpace 0)
(def kWall 1)
(def kDoor 2)
(def kUp 3)
(def kDown 4)
(def kKey 5)
(def kFood 6)
(def kMoney 7)
(def kBomb 8)
(def kMonster1 9)
(def kMonster2 10)
(def kMonster3 11)
(def kHeart 12)
(def kGenerator1 13)
(def kGenerator2 14)
(def kGenerator3 15)
(def kArrow 16)
(def kPlayer1 (+ kArrow 8))

(def kDirToDeltaX [0, 1, 1, 1, 0, -1 , -1, -1])
(def kDirToDeltaY [-1, -1, 0, 1, 1, 1, 0, -1])
(def kDeltaToDir [[7, 0, 1], [6, 0, 2], [5, 4, 3]])
(def kSearchOrder [0, -1, 1])
(def kButtonsToDir [
                     ; D U R L
                     -1, ; 0 0 0 0
                     6, ; 0 0 0 1
                     2, ; 0 0 1 0
                     -1, ; 0 0 1 1
                     0, ; 0 1 0 0
                     7, ; 0 1 0 1
                     1, ; 0 1 1 0
                     0, ; 0 1 1 1
                     4, ; 1 0 0 0
                     5, ; 1 0 0 1
                     3, ; 1 0 1 0
                     4, ; 1 0 1 1
                     -1, ; 1 1 0 0
                     6, ; 1 1 0 1
                     2, ; 1 1 1 0
                     -1  ; 1 1 1 1
                     ])

; Masks
(def kButtonLeft 1)
(def kButtonRight 2)
(def kButtonUp 4)
(def kButtonDown 8)
(def kButtonFire 16)
(def kButtonBomb 32)

(def kTicksPerMove 4)

(def dirty false)
(def currentLevel 0)
(def rotor 0)

(def px 0)
(def py 0)
(def pHealth 100)
(def pScore 0)
(def pBombs 0)
(def pKeys 0)
(def pDir)
(def pax 0)
(def pay 0)
(def paDir -1)
(def pButtons 0)
(def pOldButtons 0)
(def pPlayerMoveTimer 0)
(def encoding " *DudKF$i123mnop")

(def strike (ImageIcon. (ClassLoader/getSystemResource "dandy.png")))

(defn level-resource-path [level] (str "levels/level." (char (+ 97 level))))

(defn resource-as-stream [resource-path]
  (-> (Thread/currentThread)
    (.getContextClassLoader)
    (.getResourceAsStream resource-path)))

(defn lazy-input
  "Returns a lazy sequence of bytes (as ints) from an input stream or Reader."
  [input-stream]
  (let [step (fn step []
               (let [c (.read input-stream)]
                 (when-not (== c -1)
                   (cons c (lazy-seq (step))))))]
    (lazy-seq (step))))

(defn byte-to-nibbles [x] [(bit-and 15 x) (bit-and 15 (bit-shift-right x 4))])

(defn read-level [level]
  (with-open [r (resource-as-stream (level-resource-path level))]
    (vec (mapcat byte-to-nibbles (lazy-input r)))))

(defn print-level [level]
  (apply str (map (fn [x] (nth encoding x)) level)))

(defn dandy-app []
    (doto (JFrame. "Dandy Dungeon")
      (.add (JLabel. strike))
      (.pack)
      (.setVisible true)))

(SwingUtilities/invokeLater dandy-app)
