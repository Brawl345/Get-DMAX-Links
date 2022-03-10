package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/Brawl345/get-dmax-links/structs"
	"github.com/hellflame/argparse"
	"github.com/xuri/excelize/v2"
)

const ApiBase = "https://eu1-prod.disco-api.com"
const ShowInfoUrl = ApiBase + "/content/videos/?include=primaryChannel,primaryChannel.images,show,show.images,genres,tags,images,contentPackages&sort=-seasonNumber,-episodeNumber&filter[show.id]=%d&filter[videoType]=EPISODE&page[number]=%d&page[size]=100"
const PlayerUrl = "https://sonic-eu1-prod.disco-api.com/playback/videoPlaybackInfo/"
const UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0"
const MaxAttempts = 6

var REALMS = []string{"dmaxde", "hgtv", "tlcde"}

func getValidFileName(showName string) string {
	re := regexp.MustCompile(`[^-\w.]`)
	newName := strings.TrimSpace(showName)
	newName = strings.ReplaceAll(newName, " ", "_")
	newName = re.ReplaceAllString(newName, "")
	return newName
}

func fileExists(fileName string) bool {
	if _, err := os.Stat(fileName); err == nil {
		return true
	}
	return false
}

func contains(stack []string, needle string) bool {
	for _, v := range stack {
		if v == needle {
			return true
		}
	}

	return false
}

func doRequest(url string, token string, result interface{}) error {
	client := http.Client{}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}

	if token != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", token))
	}
	req.Header.Set("User-Agent", UserAgent)
	resp, err := client.Do(req)
	if err != nil {
		return err
	}

	if resp.StatusCode == 429 {
		return &structs.RateLimitError{}
	}

	if resp.StatusCode != 200 {
		return fmt.Errorf("got HTTP status code %d", resp.StatusCode)
	}

	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)

	if err != nil {
		return errors.New("could not read body")
	}

	if err := json.Unmarshal(body, &result); err != nil {
		return errors.New("can not unmarshal JSON")
	}

	return nil
}

func getAuthorizationToken(realm string) (string, error) {
	var result structs.GetAuthorizationTokenResponse

	err := doRequest(
		fmt.Sprintf("%s/token?realm=%s", ApiBase, realm),
		"",
		&result,
	)

	if err != nil {
		return "", err
	}

	if result.Data.Attributes.Token == "" {
		return "", errors.New("got empty token")
	}

	return result.Data.Attributes.Token, nil
}

func getShow(showId int, token string, page int) (structs.GetShowResponse, error) {
	var result structs.GetShowResponse
	err := doRequest(
		fmt.Sprintf(ShowInfoUrl, showId, page),
		token,
		&result,
	)

	if err != nil {
		return structs.GetShowResponse{}, err
	}

	if result.Meta.TotalPages == 0 || len(result.Data) == 0 {
		return structs.GetShowResponse{}, errors.New("show does not exist")
	}

	return result, nil
}

func getVideoUrl(token, episodeId string) (string, error) {
	var result structs.GetVideoUrlResponse

	err := doRequest(
		PlayerUrl+episodeId,
		token,
		&result,
	)

	if err != nil {
		return "", err
	}

	return result.Data.Attributes.Streaming.Hls.Url, nil
}

func parseArgs() (structs.Flags, error) {
	var flags structs.Flags

	parser := argparse.NewParser("get-dmax-links", `Gets direct links for DMAX and Discovery series.
	
	You need the showId of the show you want to get the links for.
	Either check the show's HTML source code (CTRL+F 'showId') or take a look at this list:
	https://gist.github.com/Akamaru/3646c47b68cccead419716f3c4a7e86e`, &argparse.ParserConfig{
		WithHint:           true,
		AddShellCompletion: true,
	})

	flags.ShowId = parser.Int("id", "showId", &argparse.Option{
		Required:   true,
		Positional: true,
		Help:       "showId of the series (check HTML page code)",
	})

	flags.Realm = parser.String("r", "realm", &argparse.Option{
		Default: REALMS[0],
		Help:    fmt.Sprintf("Site to download from. Must be one of: %s", strings.Join(REALMS, ", ")),
	})

	flags.Episode = parser.Int("e", "episode", &argparse.Option{
		Default: "0",
		Help:    "Episode of season to get (0 = all) - season MUST be set!",
	})

	flags.Season = parser.Int("s", "season", &argparse.Option{
		Default: "0",
		Help:    "Season to get (0 = all)",
	})

	if err := parser.Parse(nil); err != nil {
		return structs.Flags{}, err
	}

	if !contains(REALMS, *flags.Realm) {
		return structs.Flags{}, fmt.Errorf("unknown Realm. Must be one of: %s", strings.Join(REALMS, ", "))
	}

	if *flags.Episode > 0 && *flags.Season == 0 {
		return structs.Flags{}, errors.New("need season when downloading episodes")
	}

	if *flags.Episode < 0 || *flags.Season < 0 {
		return structs.Flags{}, errors.New("episode/season must be > 0")
	}

	return flags, nil
}

func main() {
	flags, err := parseArgs()
	if err != nil {
		fmt.Print(err.Error())
		os.Exit(0)
	}

	log.Printf("Getting Authorization token for '%s'...", *flags.Realm)
	token, err := getAuthorizationToken(*flags.Realm)
	if err != nil {
		log.Fatalln(err)
	}

	log.Println("Loading show data...")
	result, err := getShow(*flags.ShowId, token, 1)
	if err != nil {
		log.Fatalln(err)
	}

	if result.Meta.TotalPages > 1 {
		log.Println("  More than 100 videos, need to get more pages...")
		for i := 1; i < result.Meta.TotalPages; i++ {
			log.Printf("  Loading page %d...", i+1)
			moreData, err := getShow(*flags.ShowId, token, i+1)
			if err != nil {
				log.Println("Couldn't get page, skipping...")
				continue
			}
			result.Data = append(result.Data, moreData.Data...)
		}
	}

	show := structs.Show{}

	for _, inc := range result.Included {
		if inc.Type == "show" {
			show = inc.Attributes
		}
	}

	if show.Name == "" {
		show.Name = "Unknown show"
	}

	log.Printf("=> %s", show.Name)

	var episodes []structs.Episode
	if *flags.Season == 0 && *flags.Episode == 0 { // Get EVERYTHING
		episodes = append(episodes, result.Data...)
	} else if *flags.Season > 0 && *flags.Episode == 0 { // Get whole season
		for _, episode := range result.Data {
			if episode.Attributes.Season == *flags.Season {
				episodes = append(episodes, episode)
			}
		}
		if len(episodes) == 0 {
			log.Fatalln("This season does not exist")
		}
	} else { // Single episode
		for _, episode := range result.Data {
			if episode.Attributes.Season == *flags.Season && episode.Attributes.Episode == *flags.Episode {
				episodes = append(episodes, episode)
			}
		}
		if len(episodes) == 0 {
			log.Fatalln("Episode not found")
		}
	}

	if len(episodes) == 0 {
		log.Fatalln("No episodes found")
	}

	xlsx := excelize.NewFile()
	currentRow := 1
	worksheet := "Sheet1"
	xlsx.SetCellValue(worksheet, fmt.Sprintf("A%d", currentRow), "Name")
	xlsx.SetCellValue(worksheet, fmt.Sprintf("B%d", currentRow), "Description")
	xlsx.SetCellValue(worksheet, fmt.Sprintf("C%d", currentRow), "File name")
	xlsx.SetCellValue(worksheet, fmt.Sprintf("D%d", currentRow), "Link")
	xlsx.SetCellValue(worksheet, fmt.Sprintf("E%d", currentRow), "Command")
	style, _ := xlsx.NewStyle(&excelize.Style{
		Font: &excelize.Font{
			Bold: true,
		},
	})
	xlsx.SetCellStyle(worksheet, "A1", "E1", style)

	currentRow += 1

	length := len(episodes)
	rateLimitError := &structs.RateLimitError{}

	for num, episode := range episodes {
		log.Printf("Getting link %d of %d: %s", num+1, length, episode.Attributes.Name)

		var filename string
		if episode.Attributes.Season == 0 && episode.Attributes.Episode == 0 {
			filename = fmt.Sprintf("%s - %s", show.Name, episode.Attributes.Name)
		} else if episode.Attributes.Season == 0 && episode.Attributes.Episode != 0 {
			filename = fmt.Sprintf("%s - E%02d", show.Name, episode.Attributes.Episode)
		} else {
			filename = fmt.Sprintf("%s - S%02dE%02d", show.Name, episode.Attributes.Season, episode.Attributes.Episode)
		}

		xlsx.SetCellValue(worksheet, fmt.Sprintf("A%d", currentRow), episode.Attributes.Name)
		xlsx.SetCellValue(worksheet, fmt.Sprintf("B%d", currentRow), episode.Attributes.Description)
		xlsx.SetCellValue(worksheet, fmt.Sprintf("C%d", currentRow), filename)

		for attempt := 0; attempt <= MaxAttempts; attempt++ {
			if attempt == MaxAttempts {
				log.Println("Couldn't get episode")
				currentRow += 1
				break
			}
			url, err := getVideoUrl(token, episode.Id)
			if err != nil {
				if errors.As(err, &rateLimitError) {
					waittime := (attempt + 1) * 5
					log.Printf("Got rate-limited, waiting %d seconds (attempt %d of %d)", waittime, attempt+1, MaxAttempts)
					time.Sleep(time.Duration(waittime) * time.Second)
				} else {
					log.Println(err)
				}
				currentRow += 1
				continue
			}
			xlsx.SetCellValue(worksheet, fmt.Sprintf("D%d", currentRow), url)
			xlsx.SetCellValue(worksheet, fmt.Sprintf("E%d", currentRow), fmt.Sprintf("youtube-dl \"%s\" -o \"%s.mp4\"", url, filename))
			currentRow += 1
			break
		}
	}

	xlsxname := getValidFileName(show.Name) + ".xlsx"
	fileNum := 0

	for fileExists(xlsxname) {
		fileNum += 1
		xlsxname = fmt.Sprintf("%s-%d.xlsx", getValidFileName(show.Name), fileNum)
	}

	if err := xlsx.SaveAs(xlsxname); err != nil {
		log.Fatalln(err)
	}

	log.Printf("=> Saved to %s", xlsxname)
}
