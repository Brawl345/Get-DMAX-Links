package structs

import "fmt"

type GetAuthorizationTokenResponse struct {
	Data struct {
		Attributes struct {
			Token string `json:"token"`
		} `json:"attributes"`
	} `json:"data"`
}

type GetShowResponse struct {
	Data     []Episode `json:"data"`
	Included []struct {
		Attributes Show   `json:"attributes"`
		Type       string `json:"type"`
	} `json:"included"`
	Meta struct {
		TotalPages int `json:"totalPages"`
	} `json:"meta"`
	Errors struct {
	} `json:"errors"`
}

type Episode struct {
	Attributes struct {
		AlternateId string `json:"alternateId"`
		AirDate     string `json:"airDate"`
		Name        string `json:"name"`
		Description string `json:"description"`
		Episode     int    `json:"episodeNumber"`
		Season      int    `json:"seasonNumber"`
		HasDrm      bool   `json:"drmEnabled"`
	} `json:"attributes"`
	Id string `json:"id"`
}

func (e *Episode) String() string {
	return fmt.Sprintf("Staffel %d, Episode %d: %s", e.Attributes.Season, e.Attributes.Episode, e.Attributes.Name)
}

type Show struct {
	AlternateId string `json:"alternateId"`
	Name        string `json:"name"`
	Episodes    int    `json:"episodeCount"`
	Seasons     int    `json:"seasonNumber"`
}

type GetVideoUrlResponse struct {
	Data struct {
		Attributes struct {
			Streaming struct {
				Hls struct {
					Url string `json:"url"`
				} `json:"hls"`
			} `json:"streaming"`
		} `json:"attributes"`
	} `json:"data"`
}

type RateLimitError struct {
}

func (e *RateLimitError) Error() string {
	return "Too Many Requests"
}

type Flags struct {
	ShowId  *int
	Realm   *string
	Episode *int
	Season  *int
}
